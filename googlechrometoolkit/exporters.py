import logging
from enum import Enum
import copy
from tabulate import tabulate

from googlechrometoolkit.utils import FileUtils, StringUtils, DateUtils

HEADER_ROW_NUMBER = "Row #"
IGNORED_HEADERS = {HEADER_ROW_NUMBER}

LOG = logging.getLogger(__name__)


class ExportMode(Enum):
    TEXT = "text"
    CSV = "csv"
    HTML = "html"
    ALL = "all"


class Ordering(Enum):
    ASC = "ASC"
    DESC = "DESC"


class FieldType(Enum):
    SIMPLE_STR = "simple_str"
    URL = "url"
    DATETIME = "datetime"


class Field(Enum):
    """
    Display name, key, type, max length
    """
    TITLE = "Title", 'title', FieldType.SIMPLE_STR, 70
    URL = "URL", 'url', FieldType.URL, 100
    LAST_VISIT_TIME = "Last visit time", 'last_visit_time', FieldType.DATETIME, -1
    VISIT_COUNT = "Visit count", "visit_count", int, -1

    def get_key(self):
        return self.value[1]

    def get_type(self):
        return self.value[2]

    def get_max_length(self):
        return self.value[3]


class DataConverter:
    def __init__(self, src_data, fields, row_stats, truncate_dict, order_by, ordering,
                 add_row_numbers=False):
        self.src_data = src_data
        self.fields = fields
        self.headers = [f.value[0] for f in fields]
        self.row_stats = row_stats
        self.truncate_dict = truncate_dict
        self.order_by = order_by.get_key()
        self.ordering = ordering
        self.add_row_numbers = add_row_numbers

    @staticmethod
    def _modify_dict_value(row_dict, key, value, new_value):
        if value != new_value:
            row_dict[key] = new_value

    @staticmethod
    def _make_html_link(url):
        return "<a href=\"{url}\">{text}</a>".format(url=url, text=url)

    def convert(self, export_mode):
        # Make a copy of the data as other export methods may use the same data objects afterwards!
        self.src_data = copy.deepcopy(self.src_data)

        if self.order_by:
            LOG.info("Ordering data by field '%s', ordering: %s", self.order_by, self.ordering)
            reverse = False if self.ordering == Ordering.ASC else True
            self.src_data = sorted(self.src_data, key=lambda data: getattr(data, self.order_by), reverse=reverse)

        if self.add_row_numbers:
            self.fields.insert(0, HEADER_ROW_NUMBER)

        converted_data = []
        row_number = 1
        for d in self.src_data:
            row_dict = {header: getattr(d, header.get_key())
                        for header in self.fields if header not in IGNORED_HEADERS}

            # Convert all field values to str
            for k, v in row_dict.items():
                row_dict[k] = str(v)

            # Update row stats
            self.row_stats.update(row_dict)

            # Apply truncates
            for field, value in row_dict.items():
                mod_val = self.convert_str_field(field, value, export_mode)
                self._modify_dict_value(row_dict, field, value, mod_val)
                mod_val = self.convert_datetime_field(field, value)
                self._modify_dict_value(row_dict, field, value, mod_val)

            # Make row
            row = []
            if self.add_row_numbers:
                row.append(str(row_number))
            for field in self.fields:
                if field not in IGNORED_HEADERS:
                    row.append(row_dict[field])

            converted_data.append(row)
            row_number += 1

        self.row_stats.print_stats()
        return converted_data

    def convert_str_field(self, field, value, export_mode):
        truncate = self.truncate_dict[field]
        max_len = field.get_max_length()
        allowed_field_types = {FieldType.SIMPLE_STR, FieldType.URL}
        if truncate and field.get_type() in allowed_field_types and len(value) > max_len:
            orig_value = value
            value = value[0:max_len] + "..."
            LOG.debug("Truncated %s: '%s', "
                      "original length: %d, new length: %d", field, orig_value, len(orig_value), max_len)

        if export_mode == ExportMode.HTML and field.get_type() == FieldType.URL:
            value = self._make_html_link(value)
        return value

    def convert_datetime_field(self, field, value):
        truncate = self.truncate_dict[field]
        if truncate and field.get_type() == FieldType.DATETIME:
            orig_date_str = value
            date_obj = DateUtils.convert_to_datetime(orig_date_str, '%Y-%m-%d %H:%M:%S.%f')
            mod_date_str = DateUtils.convert_datetime_to_str(date_obj, "%Y-%m-%d")
            LOG.debug("Truncated date. Original value: %s, New value: %s", orig_date_str, mod_date_str)
            return mod_date_str
        return value


class ResultPrinter:
    @staticmethod
    def print_table_with_converter(converter):
        converted_data = converter.convert(ExportMode.TEXT)
        LOG.info("Printing result table: \n%s", tabulate(converted_data, converter.headers, tablefmt="fancy_grid"))

    @staticmethod
    def print_table(data, row_callback, header, print_result=True, max_width=None, max_width_separator=" "):
        converted_data = ResultPrinter._convert_list_data(
            data, row_callback, max_width=max_width, max_width_separator=max_width_separator
        )
        tabulated = tabulate(converted_data, header, tablefmt="fancy_grid")
        if print_result:
            print(tabulated)
        else:
            return tabulated

    @staticmethod
    def _convert_list_data(src_data, row_callback, max_width=None, max_width_separator=" "):
        dest_data = []
        for idx, data_row in enumerate(src_data):
            tup = row_callback(data_row)
            converted_row = [idx + 1]
            for t in tup:
                if max_width and isinstance(t, str):
                    t = StringUtils.convert_string_to_multiline(t, max_line_length=80, separator=max_width_separator)
                converted_row.append(t)
            dest_data.append(converted_row)

        return dest_data

    @staticmethod
    def print_table_html(converter, to_file):
        import html
        FileUtils.ensure_file_exists_and_writable(to_file)
        converted_data = converter.convert(ExportMode.HTML)
        tabulated = tabulate(converted_data, converter.headers, tablefmt="html")

        # Unescape manually here, as tabulate automatically escapes HTML content and there's no way to turn this off.
        tabulated = html.unescape(tabulated)

        LOG.info("Writing results to file: " + to_file)
        FileUtils.write_to_file(to_file, tabulated)

    @staticmethod
    def print_table_csv(converter, to_file):
        FileUtils.ensure_file_exists_and_writable(to_file)
        converted_data = converter.convert(ExportMode.CSV)
        tabulated = tabulate(converted_data, converter.headers, tablefmt="csv")
        LOG.info("Writing results to file: %s", to_file)
        FileUtils.write_to_file(to_file, tabulated)

    @staticmethod
    def print_table_fancy_grid(converter, to_file):
        FileUtils.ensure_file_exists_and_writable(to_file)
        converted_data = converter.convert(ExportMode.TEXT)
        tabulated = tabulate(converted_data, converter.headers, tablefmt="fancy_grid")
        LOG.info("Writing results to file: %s", to_file)
        FileUtils.write_to_file(to_file, tabulated)


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
