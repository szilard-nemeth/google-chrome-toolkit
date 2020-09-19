# Google Chrome toolkit

This project is a toolkit for Google Chrome to perform various operations that are not available in Chrome or tedious to do manually.
Currently, there are two use-cases: 
* Export browser history to various formats including CSV, HTML and simple text file. The history is read from Chrome's sqlite DB.
* Save open tabs to a text file from a connected Android device via adb.

### Getting started / Setup

You need to have python 3.8 and pip installed.
Run make from the project's root directory, all python dependencies required by the project will be installed.


## Running the tests

Currently, there are no tests added to this project.

## Main dependencies

* [sqlite3](https://docs.python.org/3.8/library/sqlite3.html) - SQLite is a C library that provides a lightweight disk-based database that doesn’t require a separate server process and allows accessing the database using a nonstandard variant of the SQL query language.
* [tabulate](https://pypi.org/project/tabulate/) - python-tabulate: Pretty-print tabular data in Python, a library and a command-line utility.
* [requests](https://requests.readthedocs.io/en/master/) - Requests: HTTP for Humans™

## Contributing

Feel free to contribute in a PR.

## Authors

* **Szilard Nemeth** - *Initial work* - [Szilard Nemeth](https://github.com/szilard-nemeth)

## Example commands

HTML export, with auto-detecting DB files: 
```
main.py --search-db-files --export-mode html
```
CSV export, with auto-detecting DB files: 
```
main.py --search-db-files --export-mode csv
```
Text export, with auto-detecting DB files: 
```
main.py --search-db-files --export-mode text
```
Export to all formats with specified profile: 
```
main.py --search-db-files --export-mode all --profile profile1
```
Export to all formats with all profiles: 
```
main.py --search-db-files --export-mode all
``` 
Export to all formats with all profiles, restricting date range: 
```
main.py -f /Users/szilardnemeth/Downloads/chromedb --search-db-files --export-mode all --from-date 2020-09-13 --to-date 2020-09-17
```
HTML export with a specified Chrome DB file: 
```
main.py -f <db_file> --export-mode html
```

Export and list DB tables:
```
main.py -f <db_file> --list-db-tables --export-mode html
```

Save all open tabs from a connected Android device: 
```
./save_open_tabs_android.py
```