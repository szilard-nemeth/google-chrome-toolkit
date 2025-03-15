#!/usr/bin/python
from typing import List

from pythoncommons.date_utils import DateUtils
from pythoncommons.file_utils import FileUtils
from pythoncommons.project_utils import ProjectUtils
from pythoncommons.string_utils import auto_str

from googlechrometoolkit.constants import GOOGLE_CHROME_HIST_DB_TEXT, GOOGLE_CHROME_HIST_DB_TEXT_PLURAL
from googlechrometoolkit.database import ChromeDb, ChromeHistoryEntry
from googlechrometoolkit.exporters import DataConverter, Field, RowStats, ResultPrinter, FieldType, Ordering, \
    ExportMode, TruncateConfig
import argparse
import sys
import logging
import os
from os.path import expanduser
import time
from logging.handlers import TimedRotatingFileHandler
from enum import Enum

__author__ = 'Szilard Nemeth'

LOG = logging.getLogger(__name__)
PROJECT_NAME = 'gchromehistoryexporter'
HISTORY_FILE_NAME = 'History'
DEFAULT_GOOGLE_CHROME_DIR = expanduser("~") + '/Library/Application Support/Google/Chrome/'
EXPORTED_DIR_NAME_PREFIX = "exported-chrome-db"
ALL_PROFILES = '*'
FILE_PROFILE_SEP = '-'
DEFAULT_FROM_DATETIME = DateUtils.get_datetime(1601, 1, 1)
DEFAULT_TO_DATETIME = DateUtils.get_datetime(2399, 1, 1)


class Extension(Enum):
    TEXT = "txt"
    CSV = "csv"
    HTML = "html"


class Setup:
    @staticmethod
    def init_logger(log_dir, console_debug=False):
        # get root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # create file handler which logs even debug messages
        log_file = ProjectUtils.get_default_log_file(PROJECT_NAME)
        fh = TimedRotatingFileHandler(os.path.join(log_dir, log_file), when='midnight')
        fh.suffix = '%Y_%m_%d.log'
        fh.setLevel(logging.DEBUG)

        # create console handler with a higher log level
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(logging.INFO)
        if console_debug:
            ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

    @staticmethod
    def parse_args_to_options():
        """This function parses and return arguments passed in"""

        # TODO make --db-files and --search-db-files mutually exclusive
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', action='store_true',
                            dest='verbose', default=None, required=False,
                            help='More verbose log')

        parser.add_argument('-l', '--list-db-tables', action='store_true',
                            dest='list_db_tables', required=False,
                            help='Whether to list DB tables of ' + GOOGLE_CHROME_HIST_DB_TEXT_PLURAL)

        parser.add_argument('--export-mode',
                            dest='export_mode',
                            type=str, choices=[mode.value for mode in ExportMode], help='Export mode',
                            required=True)

        parser.add_argument('--from-date', type=DateUtils.from_iso_format,
                            dest="from_date", help="Query history entries from this date. "
                                                   "The date must be in ISO 8601 format, for example: YYYY-MM-DD")

        parser.add_argument('--to-date', type=DateUtils.from_iso_format,
                            dest="to_date", help="Query history entries until this date. "
                                                 "The date must be in ISO 8601 format, for example: YYYY-MM-DD")

        parser.add_argument('-f', '--db-files', dest="db_files", type=FileUtils.ensure_file_exists_and_readable,
                            nargs='+', required=False)

        parser.add_argument('-t', '--truncate', dest="truncate", type=str, required=False, default=True,
                            help="Whether to truncate exported values when they are too long")

        parser.add_argument('-s', '--search-db-files', action='store_true',
                            dest='is_search_db_files', default=False,
                            required=False,
                            help='Whether to search for DB files.')

        parser.add_argument('-fm', '--filter-match',
                            required=False, help='Filter results by match criteria')

        parser.add_argument('-sb', '--search-basedir',
                            type=FileUtils.ensure_dir_created,
                            dest='search_basedir', default=DEFAULT_GOOGLE_CHROME_DIR,
                            required=False,
                            help='Basedir where this script looks for Google Chrome history DB files.')

        parser.add_argument('-p', '--profile', default=ALL_PROFILES,
                            dest='profile',
                            type=str, required=False,
                            help="Which profile to use. "
                                 "Default value is: '{}', which means export all profiles.".format(ALL_PROFILES))

        args = parser.parse_args()
        print("Args: " + str(args))
        options = Options(args)
        options.validate()
        return options


class DbResultFilter:
    def __init__(self, date_range, filter_match: str):
        self.date_range = date_range
        self.filter_match = filter_match

    def _filter_by_date(self, row):
        if self.date_range.from_date <= row.last_visit_time <= self.date_range.to_date:
            return True
        return False

    def _filter_by_match(self, row):
        if self.filter_match in row.url:
            return True
        return False

    def filter_rows(self, rows: List[ChromeHistoryEntry]):
        def get_source():
            return filtered_rows if filtered_rows else rows

        filtered_rows = None
        if self.date_range:
            LOG.info("Filtering by date range: %s", self.date_range)
            filtered_rows = list(filter(lambda row: self._filter_by_date(row), get_source()))

        if self.filter_match:
            LOG.info("Filtering entries for match by: %s", self.filter_match)
            filtered_rows = list(filter(lambda row: self._filter_by_match(row), get_source()))

        return filtered_rows


@auto_str
class DateRange:
    def __init__(self, from_date, to_date):
        self.from_date = from_date
        self.to_date = to_date

    @staticmethod
    def create(from_param, to_param):
        from_date = DEFAULT_FROM_DATETIME
        if from_param:
            from_date = DateUtils.get_datetime_from_date(from_param, min_time=True)

        to_date = DEFAULT_TO_DATETIME
        if to_param:
            to_date = DateUtils.get_datetime_from_date(to_param, min_time=True)
        return DateRange(from_date, to_date)

    @staticmethod
    def is_default_date_range(date_range):
        if date_range.from_date > DEFAULT_FROM_DATETIME or date_range.to_date < DateUtils.now():
            return False
        return True


@auto_str
class Options:
    def __init__(self, args):
        self.export_mode = ExportMode(args.export_mode)
        self.db_files = []
        if args.db_files:
            self.db_files.extend(args.db_files)
        self.is_search_db_files = args.is_search_db_files
        self.search_basedir = args.search_basedir
        self.verbose = args.verbose
        self.truncate = args.truncate
        self.date_range = DateRange.create(args.from_date, args.to_date)
        self.filter_match = args.filter_match
        self.default_range = DateRange.is_default_date_range(self.date_range)
        self.db_result_filter = DbResultFilter(self.date_range, self.filter_match)
        self.profile = args.profile
        self.is_list_db_tables = args.list_db_tables

        self.export_filename_postfix = ""
        if not self.default_range:
            from_date_str = self.date_range.from_date.strftime("%Y%m%d")
            to_date_str = self.date_range.to_date.strftime("%Y%m%d")
            self.export_filename_postfix += "__{}_{}" \
                .format(from_date_str, to_date_str)

    def validate(self):
        if self.profile and not self.is_search_db_files:
            raise ValueError("Invalid configuration. "
                             "Search DB files (option: '--search-db-files' must be specified when profile is used!")

    def __repr__(self):
        return str(self.__dict__)


class GChromeHistoryExport:
    def __init__(self, options):
        self.options = options
        self.available_profiles = None
        self.setup_dirs()

    def setup_dirs(self):
        self.project_out_root = ProjectUtils.get_output_basedir(PROJECT_NAME)
        self.search_basedir = self.options.search_basedir
        FileUtils.ensure_dir_created(self.search_basedir)

    @property
    def log_dir(self):
        return ProjectUtils.get_output_child_dir('logs')

    @property
    def exports_dir(self):
        return ProjectUtils.get_output_child_dir('exports')

    @property
    def db_copies_dir(self):
        return ProjectUtils.get_output_child_dir('db_copies')

    @staticmethod
    def get_profile_from_file_path(src_file, split_filename=True, to_lower=True) -> str:
        if split_filename:
            prof = os.path.dirname(src_file).split(os.sep)[-1]
        else:
            prof = os.path.split(src_file)[-1]
        if to_lower:
            prof = prof.lower()
        return prof.replace(" ", "")

    def process_databases(self):
        def _dst_filename_func(src_file, dest_dir):
            # Profile directory name may contains spaces, e.g. "Profile 1"
            profile: str = GChromeHistoryExport.get_profile_from_file_path(src_file)
            file_name = os.path.basename(src_file)
            return file_name + FILE_PROFILE_SEP + profile

        if self.options.is_search_db_files:
            self.search_db_files(_dst_filename_func)

        result = {}
        for db_file in self.options.db_files:
            chrome_db = ChromeDb(db_file)
            if self.options.is_list_db_tables:
                self.print_db_tables(chrome_db, db_file)
            key, filtered_rows = self.query_history_entries_from_db(chrome_db, db_file)
            result[key] = filtered_rows
        return result

    def query_history_entries_from_db(self, chrome_db, db_file):
        profile = self.get_profile_from_file_path(db_file, split_filename=False, to_lower=True)
        key = profile.split(FILE_PROFILE_SEP)[1] if FILE_PROFILE_SEP in profile else profile
        rows: List[ChromeHistoryEntry] = chrome_db.query_history_entries()
        filtered_rows = self.options.db_result_filter.filter_rows(rows)
        return key, filtered_rows

    @staticmethod
    def print_db_tables(chrome_db, db_file):
        LOG.info("Printing DB tables of %s, file: %s", GOOGLE_CHROME_HIST_DB_TEXT, db_file)
        tables, columns = chrome_db.query_db_tables()
        header = ["Row"] + columns
        tabulated = ResultPrinter.print_table(
            tables,
            lambda row: row,  # Already a tuple
            header=header,
            print_result=False,
            max_width=80,
            max_width_separator=" ",
        )
        LOG.info("\n%s", tabulated)

    def search_db_files(self, _dst_filename_func):
        """
        EXAMPLE RESULTS
        /Users/<someuser>/Library/Application Support/Google/Chrome//Profile 1/History
        /Users/<someuser>/Library/Application Support/Google/Chrome//Default/History
        /Users/<someuser>/Library/Application Support/Google/Chrome//Profile 3/History
        /Users/<someuser>/Library/Application Support/Google/Chrome//System Profile/History
        /Users/<someuser>/Library/Application Support/Google/Chrome//Guest Profile/History
        :param _dst_filename_func:
        :return:
        """
        found_db_files = FileUtils.search_files(self.search_basedir, HISTORY_FILE_NAME)
        self.available_profiles = [self.get_profile_from_file_path(file, to_lower=True)
                                   for file in found_db_files]
        if not found_db_files:
            raise ValueError("Cannot find any {} under directory: {}"
                             .format(GOOGLE_CHROME_HIST_DB_TEXT, self.search_basedir))
        LOG.info("Found DB files: \n%s", "\n".join(found_db_files))
        if self.options.profile != ALL_PROFILES and self.options.profile.lower() not in self.available_profiles:
            raise ValueError("No {} found for profile: {}. "
                             "Available profiles: {}"
                             .format(GOOGLE_CHROME_HIST_DB_TEXT, self.options.profile, self.available_profiles))

        # Make a copy of each DB file as they might be locked by Chrome if running
        msg = "Copying {}.".format(GOOGLE_CHROME_HIST_DB_TEXT) + "\n {} -> {}"
        copied_db_files = [FileUtils.copy_file_to_dir(db, self.db_copies_dir, _dst_filename_func, msg_template=msg)
                           for db in found_db_files]
        file_sizes = FileUtils.get_formatted_file_sizes_in_dir(self.db_copies_dir,
                                                               since=DateUtils.get_current_time_minus(minutes=1))
        LOG.info("Sizes of %s:\n%s", GOOGLE_CHROME_HIST_DB_TEXT, file_sizes)
        self.options.db_files.extend(copied_db_files)

    def create_new_export_dir(self):
        dt_string = DateUtils.now_formatted("%Y%m%d_%H%M%S")
        dirname = FileUtils.ensure_dir_created(os.path.join(self.exports_dir, f"{EXPORTED_DIR_NAME_PREFIX}-{dt_string}"))
        return dirname

    def get_exported_filename(self, export_dir, profile, ext_enum):
        filename = export_dir + os.sep + profile
        if self.options.export_filename_postfix != "":
            filename += self.options.export_filename_postfix
        filename += "." + ext_enum.value
        return filename

    def export(self, export_dir, converter, profile):
        html_filename = self.get_exported_filename(export_dir, profile, Extension.HTML)
        csv_filename = self.get_exported_filename(export_dir, profile, Extension.CSV)
        text_filename = self.get_exported_filename(export_dir, profile, Extension.TEXT)

        export_filenames_dict = {
            ExportMode.HTML: [html_filename],
            ExportMode.CSV: [csv_filename],
            ExportMode.TEXT: [text_filename],
            ExportMode.ALL: [html_filename, csv_filename, text_filename]
        }
        export_funcs_dict = {
            ExportMode.HTML: [ResultPrinter.print_table_html],
            ExportMode.CSV: [ResultPrinter.print_table_csv],
            ExportMode.TEXT: [ResultPrinter.print_table_fancy_grid],
            ExportMode.ALL: [
                ResultPrinter.print_table_html,
                ResultPrinter.print_table_csv,
                ResultPrinter.print_table_fancy_grid
            ]
        }
        export_mode = self.options.export_mode
        export_funcs = export_funcs_dict[export_mode]
        export_filenames = export_filenames_dict[export_mode]
        for func, filename in zip(export_funcs, export_filenames):
            ext_enum = Extension(FileUtils.get_file_extension(filename))
            LOG.info("Exporting DB to %s file", ext_enum.name)
            func(converter, filename)

    def export_by_profile(self, export_dir, entries_by_db_file, profile):
        src_data = entries_by_db_file[profile]
        all_fields = [f for f in Field]
        truncate_config = TruncateConfig()
        for f in all_fields:
            if not self.options.truncate or f.get_type() in {FieldType.DATETIME}:
                truncate_config.add_field(f, False)
            else:
                truncate_config.add_field(f, True)
        converter = DataConverter(src_data,
                                  [Field.TITLE, Field.URL, Field.LAST_VISIT_TIME, Field.VISIT_COUNT],
                                  RowStats(all_fields, track_unique=[Field.URL]),
                                  truncate_config,
                                  Field.LAST_VISIT_TIME,
                                  Ordering.DESC,
                                  add_row_numbers=True)
        self.export(export_dir, converter, profile)


def main():
    start_time = time.time()

    # Parse args
    options = Setup.parse_args_to_options()
    exporter = GChromeHistoryExport(options)

    # Initialize logging
    Setup.init_logger(exporter.log_dir, console_debug=options.verbose)

    # Start exporting
    entries_by_db_file = exporter.process_databases()

    profile = exporter.options.profile
    export_dir = exporter.create_new_export_dir()
    if profile == ALL_PROFILES:
        LOG.info("Exporting all %s...", GOOGLE_CHROME_HIST_DB_TEXT_PLURAL)
        for profile in exporter.available_profiles:
            exporter.export_by_profile(export_dir, entries_by_db_file, profile)
    else:
        # Single profile
        LOG.info("Exporting %s for single profile: %s", GOOGLE_CHROME_HIST_DB_TEXT, profile)
        exporter.export_by_profile(export_dir, entries_by_db_file, profile)

    LOG.info("Execution of script took %d seconds", time.time() - start_time)


if __name__ == '__main__':
    main()
