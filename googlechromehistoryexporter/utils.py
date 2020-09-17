import errno
import logging
import os
import string
import unicodedata

from tabulate import tabulate

LOG = logging.getLogger(__name__)


def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls


class StringUtils:

    @staticmethod
    def replace_special_chars(unistr):
        if not isinstance(unistr, unicode):
            LOG.warning("Object expected to be unicode: " + str(unistr))
            return str(unistr)
        normalized = unicodedata.normalize('NFD', unistr).encode('ascii', 'ignore')
        normalized = normalized.decode('utf-8')
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_title = ''.join(c for c in normalized if c in valid_chars)
        return valid_title


class FileUtils:
    @classmethod
    def ensure_dir_created(cls, dirname):
        """
    Ensure that a named directory exists; if it does not, attempt to create it.
    """
        try:
            os.makedirs(dirname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return dirname


class ResultPrinter:
    def __init__(self, data, headers):
        self.data = data
        self.headers = headers

    def print_table(self):
        LOG.info("Printing result table: %s", tabulate(self.data, self.headers, tablefmt="fancy_grid"))

    def print_table_html(self):
        LOG.info("Printing result table: %s", tabulate(self.data, self.headers, tablefmt="html"))


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