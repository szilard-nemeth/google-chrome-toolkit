import datetime
import logging

from tabulate import tabulate

LOG = logging.getLogger(__name__)
PRINTABLE_FIELD_DISPLAY_NAMES = ["Name", "Link", "Shared with me date", "Owner", "Type"]
TITLE_MAX_LENGTH = 50
LINK_MAX_LENGTH = 20


def convert_data_to_rows(data, truncate=False):
    converted_data = []
    truncate_links = truncate
    truncate_titles = truncate
    truncate_dates = truncate

    row_stats = RowStats(["name", "link", "date", "owners", "type"], track_unique=["type"])
    for f in data:
        name = str(f.name)
        link = str(f.link)
        date = str(f.shared_with_me_date)
        owners = ",".join([o.name for o in f.owners])
        # mimetype = self._convert_mime_type(str(f.mime_type))

        row_stats.update({"name": name, "link": link, "date": date, "owners": owners, "type": mimetype})

        if truncate_titles and len(name) > TITLE_MAX_LENGTH:
            original_name = name
            name = name[0:TITLE_MAX_LENGTH] + "..."
            LOG.debug("Truncated title: '%s', original length: %d, new length: %d",
                      original_name, len(original_name), TITLE_MAX_LENGTH)

        if truncate_links:
            original_link = link
            link = link[0:LINK_MAX_LENGTH]
            LOG.debug("Truncated link: '%s', original length: %d, new length: %d",
                      original_link, len(original_link), LINK_MAX_LENGTH)

        if truncate_dates:
            original_date = date
            date_obj = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
            date = date_obj.strftime("%Y-%m-%d")
            LOG.debug("Truncated date: '%s', original value: %s, new value: %s",
                      original_date, original_date, date)

        row = [name, link, date, owners, mimetype]
        converted_data.append(row)
    row_stats.print_stats()
    return converted_data


def print_results_table(self):
    if not self.data:
        raise ValueError("Data is not yet set, please call sync method first!")
    result_printer = ResultPrinter(self.data, self.headers)
    result_printer.print_table()


class RowStats:
    def __init__(self, list_of_fields, track_unique=None):
        self.list_of_fields = list_of_fields
        self.longest_fields = {}
        self.unique_values = {}
        for f in list_of_fields:
            self.longest_fields[f] = ""
        self.longest_line = ""

        self.track_unique_values = track_unique
        if not self.track_unique_values:
            self.track_unique_values = []

    def update(self, row_dict):
        # Update longest fields dict values if required
        for field_name in self.list_of_fields:
            self._update_field(field_name, row_dict[field_name])

        for field_name in self.track_unique_values:
            if field_name not in self.unique_values:
                self.unique_values[field_name] = set()
            self.unique_values[field_name].add(row_dict[field_name])

        # Store longest line
        sum_length = 0
        for field_name in self.list_of_fields:
            sum_length += len(row_dict[field_name])
        if sum_length > len(self.longest_line):
            self.longest_line = ",".join(row_dict.values())

    def _update_field(self, field_name, field_value):
        if len(field_value) > len(self.longest_fields[field_name]):
            self.longest_fields[field_name] = field_value

    def print_stats(self):
        LOG.info("Longest line is: '%s' (%d characters)", self.longest_line, len(self.longest_line))
        for field_name in self.track_unique_values:
            self._print(field_name)

        if len(self.unique_values) > 0:
            for field_name, values_set in self.unique_values.items():
                LOG.info("Unique values of field '%s': %s", field_name, ",".join(values_set))

    def _print(self, field_name):
        field_value = self.longest_fields[field_name]
        LOG.info("Longest %s is: '%s' (length: %d characters)", field_name, field_value, len(field_value))


class ResultPrinter:
    def __init__(self, data, headers):
        self.data = data
        self.headers = headers

    def print_table(self):
        LOG.info("Printing result table: %s", tabulate(self.data, self.headers, tablefmt="fancy_grid"))

    def print_table_html(self):
        LOG.info("Printing result table: %s", tabulate(self.data, self.headers, tablefmt="html"))