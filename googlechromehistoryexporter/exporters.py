import datetime
import logging
from enum import Enum

from tabulate import tabulate

from googlechromehistoryexporter.utils import FileUtils

LOG = logging.getLogger(__name__)


class Field(Enum):
    """
    Display name, key, type, max length
    """
    TITLE = "Title", 'title', str, 70
    URL = "URL", 'url', str, 100
    LAST_VISIT_TIME = "Last visit time", 'last_visit_time', 'datetime', -1
    VISIT_COUNT = "Visit count", "visit_count", int, -1

    def get_key(self):
        return self.value[1]

    def get_type(self):
        return self.value[2]

    def get_max_length(self):
        return self.value[3]


class DataConverter:
    def __init__(self, src_data, headers, row_stats, truncate_dict, order_by, order_mode, add_row_numbers=False):
        self.src_data = src_data
        self.headers = headers
        self.row_stats = row_stats
        self.truncate_dict = truncate_dict
        self.order_by = order_by.get_key()
        self.order_mode = order_mode
        self.add_row_numbers = add_row_numbers

    @staticmethod
    def _modify_dict_value(row_dict, key, value, new_value):
        if value != new_value:
            row_dict[key] = new_value

    def convert(self):
        if self.order_by:
            LOG.info("Ordering data by field '%s', mode: %s", self.order_by, self.order_mode)
            reverse = False if self.order_mode == "ASC" else True
            self.src_data = sorted(self.src_data, key=lambda data: getattr(data, self.order_by), reverse=reverse)

        converted_data = []
        row_number = 1
        for d in self.src_data:
            row_dict = {header: getattr(d, header.get_key()) for header in self.headers}

            # Convert all fields to str
            for k, v in row_dict.items():
                row_dict[k] = str(v)

            # Update row stats
            self.row_stats.update(row_dict)

            # Apply truncates
            for field, value in row_dict.items():
                mod_val = self.convert_str_field(field, value)
                self._modify_dict_value(row_dict, field, value, mod_val)
                mod_val = self.convert_datetime_field(field, value)
                self._modify_dict_value(row_dict, field, value, mod_val)

            # Make row
            row = []
            if self.add_row_numbers:
                row.append(str(row_number))
            for field in self.headers:
                row.append(row_dict[field])

            converted_data.append(row)
            row_number += 1

        if self.add_row_numbers:
            self.headers.insert(0, "Row #")
        self.row_stats.print_stats()
        return converted_data

    def convert_str_field(self, field, value):
        truncate = self.truncate_dict[field]
        max_len = field.get_max_length()
        if truncate and field.get_type() == str and len(value) > max_len:
            orig_value = value
            mod_value = value[0:max_len] + "..."
            LOG.debug("Truncated %s: '%s', "
                      "original length: %d, new length: %d", field, orig_value, len(orig_value), max_len)
            return mod_value
        return value

    def convert_datetime_field(self, field, value):
        truncate = self.truncate_dict[field]
        if truncate and field.get_type() == 'datetime':
            orig_date = value
            date_obj = datetime.datetime.strptime(orig_date, '%Y-%m-%d %H:%M:%S.%f')
            mod_date = date_obj.strftime("%Y-%m-%d")
            LOG.debug("Truncated date: '%s', original value: %s, new value: %s", orig_date, orig_date, mod_date)
            return mod_date
        return value


class ResultPrinter:
    @staticmethod
    def print_table(converter):
        converted_data = converter.convert()
        LOG.info("Printing result table: \n%s", tabulate(converted_data, converter.headers, tablefmt="fancy_grid"))

    @staticmethod
    def print_table_html(converter, to_file=None):
        converted_data = converter.convert()
        tabulated = tabulate(converted_data, converter.headers, tablefmt="html")
        if to_file:
            LOG.info("Writing results to file: " + to_file)
            FileUtils.write_to_file(to_file, tabulated)
        else:
            LOG.info("Printing result table: \n%s", tabulated)


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
        LOG.debug("Longest line is %d characters long", len(self.longest_line))
        for field_name in self.track_unique_values:
            self._print(field_name)

        if len(self.unique_values) > 0:
            for field_name, values_set in self.unique_values.items():
                LOG.info("Number of unique values of field '%s': %d", field_name, len(values_set))

    def _print(self, field_name):
        field_value = self.longest_fields[field_name]
        LOG.debug("Longest line is %d characters long. Field name: %s", len(field_value), field_name)
