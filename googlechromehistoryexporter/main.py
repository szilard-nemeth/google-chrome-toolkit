#!/usr/bin/python
from googlechromehistoryexporter.exporters import DataConverter, Field, RowStats, ResultPrinter, FieldType

__author__ = 'Szilard Nemeth'
import argparse
import sys
import datetime as dt
import logging
import os
import sqlite3
from os.path import expanduser
import datetime
import time
from logging.handlers import TimedRotatingFileHandler
from enum import Enum

from googlechromehistoryexporter.utils import auto_str, FileUtils

LOG = logging.getLogger(__name__)
PROJECT_NAME = 'gchromehistoryexporter'
HISTORY_FILE_NAME = 'History'
DEFAULT_GOOGLE_CHROME_DIR = expanduser("~") + '/Library/Application Support/Google/Chrome/'
EXPORTED_DIR_NAME = "exported-chrome-db"


class ExportMode(Enum):
    TEXT = "text"
    CSV = "csv"
    HTML = "html"

@auto_str
class ChromeHistoryEntry:
    def __init__(self, title, url, last_visit_time, visit_count):
        self.title = title
        self.url = url
        self.last_visit_time = last_visit_time
        self.visit_count = visit_count

    def __repr__(self):
        return str(self.__dict__)


class Setup:
    @staticmethod
    def init_logger(log_dir, console_debug=False):
        # get root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # create file handler which logs even debug messages
        log_file_name = datetime.datetime.now().strftime(
            (PROJECT_NAME + '-%Y_%m_%d_%H%M%S.log'))

        fh = TimedRotatingFileHandler(os.path.join(log_dir, log_file_name), when='midnight')
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

        parser = argparse.ArgumentParser()
        # TODO make --db-files and --lookup-db-files mutually exclusive
        # TODO add argument - profile: Only export one DB for a profile

        parser.add_argument('-v', '--verbose', action='store_true',
                            dest='verbose', default=None, required=False,
                            help='More verbose log')

        parser.add_argument('--export-mode',
                            dest='export_mode',
                            type=str, choices=[mode.value for mode in ExportMode], help='Export mode',
                            required=True)

        parser.add_argument('-f', '--db-files', dest="db_files", type=FileUtils.ensure_file_exists_and_readable,
                            nargs='+', required=True)

        parser.add_argument('-t', '--truncate', dest="truncate", type=str, required=False, default=True,
                            help="Whether to truncate exported values when they are too long")

        parser.add_argument('-s', '--search-db-files', action='store_true',
                            dest='search_db_files', default=False,
                            required=False,
                            help='Whether to search for DB files.')
        parser.add_argument('-sb', '--search-basedir',
                            type=FileUtils.ensure_dir_created,
                            dest='search_basedir', default=DEFAULT_GOOGLE_CHROME_DIR,
                            required=False,
                            help='Basedir where this script looks for Google Chrome history DB files.')

        args = parser.parse_args()
        print("Args: " + str(args))
        return Options(args)


@auto_str
class Options:
    def __init__(self, args):
        self.export_mode = ExportMode(args.export_mode)
        self.db_files = args.db_files
        self.search_db_files = args.search_db_files
        self.search_basedir = args.search_basedir
        self.verbose = args.verbose
        self.truncate = args.truncate

    def __repr__(self):
        return str(self.__dict__)


class GChromeHistoryExport:
    def __init__(self, options):
        # Options
        self.options = options
        self.search_db_files = options.search_db_files

        # Setup Directories
        self.project_out_root = None
        self.log_dir = None
        self.exports_dir = None
        self.db_copies_dir = None
        self.search_basedir = None
        self.setup_dirs()

    def setup_dirs(self):
        home = expanduser("~")
        self.project_out_root = os.path.join(home, PROJECT_NAME)
        FileUtils.ensure_dir_created(self.project_out_root)

        self.log_dir = os.path.join(self.project_out_root, 'logs')
        FileUtils.ensure_dir_created(self.log_dir)

        self.exports_dir = os.path.join(self.project_out_root, 'exports')
        FileUtils.ensure_dir_created(self.exports_dir)

        self.db_copies_dir = os.path.join(self.project_out_root, 'db_copies')
        FileUtils.ensure_dir_created(self.db_copies_dir)

        self.search_basedir = options.search_basedir
        FileUtils.ensure_dir_created(self.search_basedir)

    @staticmethod
    def get_profile_from_file_path(src_file, split_filename=True):
        if split_filename:
            profile = os.path.dirname(src_file).split('/')[-1]
        else:
            profile = os.path.split(src_file)[-1]
        return profile.replace(" ", "")

    def query_history_entries(self):
        def _dst_filename_func(src_file, dest_dir):
            # Profile directory name may contains spaces, e.g. "Profile 1"
            profile = GChromeHistoryExport.get_profile_from_file_path(src_file)
            file_name = os.path.basename(src_file)
            return file_name + '-' + profile

        if self.search_db_files:
            found_db_files = FileUtils.search_files(self.search_basedir, HISTORY_FILE_NAME)
            LOG.info("Found DB files: \n%s", "\n".join(found_db_files))
            # EXAMPLE RESULTS
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Profile 1/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Default/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Profile 3/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//System Profile/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Guest Profile/History
            if not found_db_files:
                raise ValueError("Cannot find any DB file under directory: " + self.search_basedir)

            # Make a copy of each db file as they might be locked by Chrome
            copied_db_files = [FileUtils.copy_file_to_dir(db, self.db_copies_dir, _dst_filename_func) for db in found_db_files]
            file_sizes = FileUtils.get_file_sizes_in_dir(self.db_copies_dir)
            LOG.info("Sizes of copied DB files:\n%s", file_sizes)
            self.options.db_files.extend(copied_db_files)

        result = {}
        for db_file in self.options.db_files:
            LOG.info("Using DB file: %s", db_file)
            self.query_databases(db_file)
            hist_entries = self.query_data_from_db(db_file)
            key = GChromeHistoryExport.get_profile_from_file_path(db_file, split_filename=False)
            result[key] = hist_entries
        return result

    @staticmethod
    def query_databases(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        LOG.info("Listing available databases: ")
        for row in c.execute("SELECT * FROM main.sqlite_master WHERE type='table'"):
            # TODO list this with tabulate
            LOG.info(row)

    @staticmethod
    def query_data_from_db(db_file):
        def _convert_chrome_datetime(microseconds):
            """
            Since Google Chrome stores the last visit time with microseconds passed since 1601-01-01T00:00:00Z (Windows epoch),
            the number of milliseconds of stored date need to be added to the date of 1601-01-01 to get the correct date value.
            :param microseconds:
            :return:
            """
            return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=microseconds)

        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        query = "select title, url, last_visit_time, visit_count from urls order by last_visit_time desc"
        c.execute(query)
        results = c.fetchall()
        result_objs = [ChromeHistoryEntry(r[0], r[1], _convert_chrome_datetime(r[2]), r[3]) for r in results]
        return result_objs

    def create_new_export_dir(self):
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        dirname = FileUtils.ensure_dir_created(os.path.join(self.exports_dir, EXPORTED_DIR_NAME + '-' + dt_string))
        return dirname


if __name__ == '__main__':
    start_time = time.time()

    # Parse args
    options = Setup.parse_args_to_options()
    exporter = GChromeHistoryExport(options)

    # Initialize logging
    Setup.init_logger(exporter.log_dir, console_debug=options.verbose)

    # Start exporting
    entries_by_db_file = exporter.query_history_entries()

    # TODO control this by CLI argument
    profile = HISTORY_FILE_NAME + "-Profile1"
    src_data = entries_by_db_file[profile]
    all_fields = [f for f in Field]

    truncate_dict = {}
    for f in all_fields:
        if not exporter.options.truncate or f.get_type() in {FieldType.DATETIME}:
            truncate_dict[f] = False
        else:
            truncate_dict[f] = True

    converter = DataConverter(src_data,
                              [Field.TITLE, Field.URL, Field.LAST_VISIT_TIME, Field.VISIT_COUNT],
                              exporter.options.export_mode,
                              RowStats(all_fields, track_unique=[Field.URL]),
                              truncate_dict,
                              Field.LAST_VISIT_TIME,
                              'DESC',
                              add_row_numbers=True)

    export_dir = exporter.create_new_export_dir()
    if exporter.options.export_mode == ExportMode.HTML:
        file = export_dir + os.sep + profile + ".html"
        ResultPrinter.print_table_html(converter, file)
    elif exporter.options.export_mode == ExportMode.CSV:
        file = export_dir + os.sep + profile + ".csv"
        ResultPrinter.print_table_csv(converter, file)
    elif exporter.options.export_mode == ExportMode.TEXT:
        file = export_dir + os.sep + profile + ".txt"
        ResultPrinter.print_table_fancy_grid(converter, file)

    end_time = time.time()
    LOG.info("Execution of script took %d seconds", end_time - start_time)
