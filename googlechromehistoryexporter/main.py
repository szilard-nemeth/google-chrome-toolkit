#!/usr/bin/python
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


class OperationMode(Enum):
    EXPORT_TEXT = "EXPORT_TEXT"
    EXPORT_CSV = "EXPORT_CSV"
    PRINT = "PRINT"


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

        parser.add_argument('-v', '--verbose', action='store_true',
                            dest='verbose', default=None, required=False,
                            help='More verbose log')

        parser.add_argument('-p', '--print', nargs='+', type=str, dest='print',
                            help='Print results to console',
                            required=False)
        parser.add_argument('-c', '--csv', action='store_true',
                            dest='csv', default=False,
                            required=False,
                            help='Export entries to a CSV file.')
        parser.add_argument('-t', '--text', action='store_true',
                            dest='text', default=False,
                            required=False,
                            help='Export entries to a text file separated by newlines.')

        # TODO make --db-files and --lookup-db-files mutually exclusive
        parser.add_argument('-f', '--db-files', dest="db_files", type=FileUtils.ensure_file_exists_and_readable, nargs='+', required=True)

        parser.add_argument('-s', '--search-db-files', action='store_true',
                            dest='search_db_files', default=False,
                            required=False,
                            help='Whether to search for db files.')
        parser.add_argument('-sb', '--search-basedir',
                            type=FileUtils.ensure_dir_created,
                            dest='search_basedir', default=DEFAULT_GOOGLE_CHROME_DIR,
                            required=False,
                            help='Basedir where this script looks for Google Chrome history db files.')


        # TODO add parameter that can read multiple db files

        args = parser.parse_args()
        print("Args: " + str(args))

        operation_mode = None
        if args.print:
            operation_mode = OperationMode.PRINT
        elif args.csv:
            operation_mode = OperationMode.EXPORT_CSV
        elif args.text:
            operation_mode = OperationMode.EXPORT_TEXT
        if not operation_mode:
            LOG.warning("Operation mode has not been provided! Falling back to Print mode.")
            operation_mode = OperationMode.PRINT

        options = Options(operation_mode, args.db_files, args.search_db_files, args.search_basedir, args.verbose)
        return options


@auto_str
class Options:
    def __init__(self, operation_mode, db_files, search_db_files, search_basedir, verbose):
        self.operation_mode = operation_mode
        self.db_files = db_files
        self.search_db_files = search_db_files
        self.search_basedir = search_basedir
        self.verbose = verbose

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

        # Validation
        self.validate_operation_mode(options.operation_mode)

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
    def validate_operation_mode(provided_op_mode):
        valid_op_modes = [e.name for e in OperationMode]
        if provided_op_mode and provided_op_mode.name not in valid_op_modes:
            raise ValueError("Unknown Operation mode, should be any of these: {}".format(valid_op_modes))
        LOG.info("Using operation mode: %s", options.operation_mode)

    def query_history_entries(self):
        def _dst_filename_func(src_file, dest_dir):
            # Profile directory name may contains spaces, e.g. "Profile 1"
            profile = os.path.dirname(src_file).split('/')[-1]
            profile = profile.replace(" ", "")
            file_name = os.path.basename(src_file)
            return file_name + '-' + profile


        if self.search_db_files:
            found_db_files = FileUtils.search_files(self.search_basedir, HISTORY_FILE_NAME)
            LOG.info("Found db files: \n%s", "\n".join(found_db_files))
            # EXAMPLE RESULTS
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Profile 1/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Default/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Profile 3/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//System Profile/History
            # /Users/<someuser>/Library/Application Support/Google/Chrome//Guest Profile/History
            if not found_db_files:
                raise ValueError("Cannot find any db file under directory: " + self.search_basedir)

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
            result[db_file] = hist_entries
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
        # LOG.debug("Results: " + str(result_objs))
        return result_objs


if __name__ == '__main__':
    start_time = time.time()

    # Parse args
    options = Setup.parse_args_to_options()
    gchrome_export = GChromeHistoryExport(options)

    # Initialize logging
    Setup.init_logger(gchrome_export.log_dir, console_debug=options.verbose)

    # Start exporting
    entries_by_db_file = gchrome_export.query_history_entries()

    # TODO
    #truncate = self.options.operation_mode == OperationMode.PRINT
    # self.data = self.convert_data_to_rows(db_data, truncate=truncate)
    # self.print_results_table()

    end_time = time.time()
    LOG.info("Execution of script took %d seconds", end_time - start_time)
