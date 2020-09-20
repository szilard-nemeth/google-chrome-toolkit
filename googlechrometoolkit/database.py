import logging
import sqlite3

from pythoncommons.date_utils import DateUtils
from pythoncommons.string_utils import auto_str

from googlechrometoolkit.constants import GOOGLE_CHROME_HIST_DB_TEXT

LOG = logging.getLogger(__name__)


@auto_str
class ChromeHistoryEntry:
    def __init__(self, title, url, last_visit_time, visit_count):
        self.title = title
        self.url = url
        self.last_visit_time = last_visit_time
        self.visit_count = visit_count

    def __repr__(self):
        return str(self.__dict__)


class ChromeDb:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)

    def query_db_tables(self):
        cursor = self.conn.cursor()
        LOG.info("Listing available DB tables of %s: %s", GOOGLE_CHROME_HIST_DB_TEXT, self.db_file)
        cursor.execute("SELECT * FROM main.sqlite_master WHERE type='table'")
        columns = list(map(lambda x: x[0], cursor.description))
        result = cursor.fetchall()
        return result, columns

    def query_history_entries(self):
        def _convert_chrome_datetime(microseconds):
            """
            Since Google Chrome stores the last visit time with microseconds passed since
            1601-01-01T00:00:00Z (Windows epoch),
            the number of milliseconds of stored date need to be added to the date of
            1601-01-01 to get the correct date value.
            :param microseconds:
            :return:
            """
            return DateUtils.add_microseconds_to_win_epoch(microseconds)

        c = self.conn.cursor()
        query = "select title, url, last_visit_time, visit_count from urls order by last_visit_time desc"
        c.execute(query)
        results = c.fetchall()
        result_objs = [ChromeHistoryEntry(r[0], r[1], _convert_chrome_datetime(r[2]), r[3]) for r in results]
        return result_objs
