
1. Cd into Chrome dir:
`cd /Users/szilardnemeth/Library/Application\ Support/Google/Chrome/Profile\ 1`

2. Run this command: `find . -print0 | xargs -0 file | grep -i sqlite`
```
szilardnemeth@snemeth-MBP [14:28:09] •100% --( ~/Library/Application Support/Google/Chrome/Profile 1 ) 
➜ find . -print0 | xargs -0 file | grep -i sqlite
./previews_opt_out.db:                                                                                                                                    SQLite 3.x database, last written using SQLite version 3020001
./Extension Cookies:                                                                                                                                      SQLite 3.x database, last written using SQLite version 3032001
./Favicons:                                                                                                                                               SQLite 3.x database, last written using SQLite version 3032001
./Web Data:                                                                                                                                               SQLite 3.x database, last written using SQLite version 3032001
./heavy_ad_intervention_opt_out.db:                                                                                                                       SQLite 3.x database, last written using SQLite version 3029000
./Login Data:                                                                                                                                             SQLite 3.x database, last written using SQLite version 3032001
./Reporting and NEL:                                                                                                                                      SQLite 3.x database, last written using SQLite version 3032001
./Network Action Predictor:                                                                                                                               SQLite 3.x database, last written using SQLite version 3032001
./Storage/ext/gaedmjdfmmahhbjefcbgaolhhanlaolb/def/databases/Databases.db:                                                                                SQLite 3.x database, last written using SQLite version 3020001
./Storage/ext/gaedmjdfmmahhbjefcbgaolhhanlaolb/def/Reporting and NEL:                                                   SQLite 3.x database, last written using SQLite version 3030001
./Storage/ext/gaedmjdfmmahhbjefcbgaolhhanlaolb/def/QuotaManager:                                                        SQLite 3.x database, last written using SQLite version 3030001
./Storage/ext/gaedmjdfmmahhbjefcbgaolhhanlaolb/def/Cookies:                                                             SQLite 3.x database, last written using SQLite version 3030001
./Storage/ext/knipolnnllmklapflnccelgolnpehhpl/def/Reporting and NEL:                                                   SQLite 3.x database, last written using SQLite version 3030001
./Storage/ext/knipolnnllmklapflnccelgolnpehhpl/def/Cookies:                                                             SQLite 3.x database, last written using SQLite version 3030001
./Application Cache/Index:                                                                                               SQLite 3.x database, last written using SQLite version 3032001
./Affiliation Database:                                                                                                  SQLite 3.x database, last written using SQLite version 3020001
./History:                                                                                                               SQLite 3.x database, last written using SQLite version 3032001
./Shortcuts:                                                                                                             SQLite 3.x database, last written using SQLite version 3032001
./QuotaManager:                                                                                                          SQLite 3.x database, last written using SQLite version 3032001
./Sync Data/SyncData.sqlite3:                                                                                            SQLite 3.x database, last written using SQLite version 3032001
./Sync Data/SyncData.sqlite3-journal:                                                                                    empty
./Top Sites:                                                                                                             SQLite 3.x database, last written using SQLite version 3032001
./Cookies:                                                                                                               SQLite 3.x database, last written using SQLite version 3032001
./Media History:                                                                                                         SQLite 3.x database, last written using SQLite version 3032001
```