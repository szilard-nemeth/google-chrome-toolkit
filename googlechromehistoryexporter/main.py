#!/usr/bin/python

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

from googlechromehistoryexporter.utils import auto_str, FileUtils, ResultPrinter, RowStats

LOG = logging.getLogger(__name__)
PROJECT_NAME = 'gchromehistoryexporter'
PRINTABLE_FIELD_DISPLAY_NAMES = ["Name", "Link", "Shared with me date", "Owner", "Type"]
__author__ = 'Szilard Nemeth'


class OperationMode(Enum):
    EXPORT_TEXT = "EXPORT_TEXT"
    EXPORT_CSV = "EXPORT_CSV"
    PRINT = "PRINT"


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
        parser.add_argument('-f', '--db-files', dest="db_files", type=argparse.FileType('r'), nargs='+', required=True)

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

        options = Options(operation_mode, args.db_files, args.verbose)
        return options


@auto_str
class Options:
    def __init__(self, operation_mode, db_files, verbose):
        self.operation_mode = operation_mode
        self.db_files = db_files
        self.verbose = verbose

    def __repr__(self):
        return str(self.__dict__)


class GChromeHistoryExport:
    def __init__(self, options):
        # Options
        self.options = options

        # Setup Directories
        self.project_out_root = None
        self.log_dir = None
        self.exports_dir = None
        self.setup_dirs()

        # Validation
        self.validate_operation_mode(options.operation_mode)

    def setup_dirs(self):
        home = expanduser("~")
        self.project_out_root = os.path.join(home, PROJECT_NAME)
        self.log_dir = os.path.join(self.project_out_root, 'logs')
        self.exports_dir = os.path.join(self.project_out_root, 'exports')
        FileUtils.ensure_dir_created(self.project_out_root)
        FileUtils.ensure_dir_created(self.log_dir)
        FileUtils.ensure_dir_created(self.exports_dir)

    @staticmethod
    def validate_operation_mode(provided_op_mode):
        valid_op_modes = [e.name for e in OperationMode]
        if provided_op_mode and provided_op_mode not in valid_op_modes:
            raise ValueError("Unknown Operation mode, should be any of these: {}".format(valid_op_modes))
        LOG.info("Using operation mode: %s", options.operation_mode)

    def export(self):
        raw_data_from_api = self.get_data_from_db()
        # TODO debug log raw data here
        truncate = self.operation_mode == OperationMode.PRINT
        self.data = self.convert_data_to_rows(raw_data_from_api, truncate=truncate)
        self.print_results_table()

    def get_data_from_db(self):
        conn = sqlite3.connect('example.db')
        c = conn.cursor()
        timestamp = ('1000000-11644473600',)
        query = "select datetime(last_visit_time/?,'unixepoch') as 'date', url from urls order by last_visit_time desc"
        c.execute(query, timestamp)

    def print_results_table(self):
        if not self.data:
            raise ValueError("Data is not yet set, please call sync method first!")
        result_printer = ResultPrinter(self.data, self.headers)
        result_printer.print_table()

    def convert_data_to_rows(self, data, truncate=False):
        TITLE_MAX_LENGTH = 50
        LINK_MAX_LENGTH = 20
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
            #mimetype = self._convert_mime_type(str(f.mime_type))

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
                date_obj = dt.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
                date = date_obj.strftime("%Y-%m-%d")
                LOG.debug("Truncated date: '%s', original value: %s, new value: %s",
                          original_date, original_date, date)

            row = [name, link, date, owners, mimetype]
            converted_data.append(row)
        row_stats.print_stats()
        return converted_data



if __name__ == '__main__':
    start_time = time.time()

    # Parse args
    options = Setup.parse_args_to_options()
    gchrome_export = GChromeHistoryExport(options)

    # Initialize logging
    Setup.init_logger(gchrome_export.log_dir, console_debug=options.verbose)

    # Start exporting
    gchrome_export.export()
    end_time = time.time()
    LOG.info("Execution of script took %d seconds", end_time - start_time)
