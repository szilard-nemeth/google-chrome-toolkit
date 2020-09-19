
1. Cd into Chrome dir:
`cd /Users/szilardnemeth/Library/Application\ Support/Google/Chrome/Profile\ 1`

2. Run this command: `find . -print0 | xargs -0 file | grep -i sqlite`
```
szilardnemeth@snemeth-MBP [14:28:09] •100% --( ~/Library/Application Support/Google/Chrome/Profile 1 ) 
➜ find . -print0 | xargs -0 file | grep -i sqlite
./previews_opt_out.db:                                                                                                                                    SQLite 3.x database, last written using SQLite version 3020001
./databases/chrome-extension_dhdgffkkebhmkfjojejmpbldmpobfkfo_0/21:                                                                                       SQLite 3.x database, last written using SQLite version 3026000
./databases/chrome-extension_hdokiejnpimakedhajhdlcegeplioahd_0/1:                                                                                        SQLite 3.x database, last written using SQLite version 3032001
./databases/https_www.ebay.co.uk_0/43:                                                                                                                    SQLite 3.x database, last written using SQLite version 3030001
./databases/https_signin.ebay.com_0/34:                                                                                                                   SQLite 3.x database, last written using SQLite version 3030001
./databases/https_www.vatera.hu_0/22:                                                                                                                     SQLite 3.x database, last written using SQLite version 3026000
./databases/https_mail.google.com_0/55:                                                                                                                   SQLite 3.x database, last written using SQLite version 3032001
./databases/https_translate.google.com_0/26:                                                                                                              SQLite 3.x database, last written using SQLite version 3027002
./databases/https_translate.google.com_0/25:                                                                                                              SQLite 3.x database, last written using SQLite version 3027002
./databases/https_pay.ebay.com_0/54:                                                                                                                      SQLite 3.x database, last written using SQLite version 3032001
./databases/https_secure.esky.hu_0/28:                                                                                                                    SQLite 3.x database, last written using SQLite version 3027002
./databases/https_wwws.klm.hu_0/30:                                                                                                                       SQLite 3.x database, last written using SQLite version 3027002
./databases/https_www.klm.ch_0/29:                                                                                                                        SQLite 3.x database, last written using SQLite version 3027002
./databases/https_www.ebay.com_0/33:                                                                                                                      SQLite 3.x database, last written using SQLite version 3032001
./databases/https_signin.ebay.co.uk_0/44:                                                                                                                 SQLite 3.x database, last written using SQLite version 3030001
./databases/Databases.db:                                                                                                                                 SQLite 3.x database, last written using SQLite version 3032001
./databases/https_fal.444.hu_0/49:                                                                                                                        SQLite 3.x database, last written using SQLite version 3030001
./databases/https_transferwise.com_0/16:                                                                                                                  SQLite 3.x database, last written using SQLite version 3031001
./databases/https_magyarnarancs.hu_0/50:                                                                                                                  SQLite 3.x database, last written using SQLite version 3030001
./databases/chrome-extension_edacconmaakjimmfgnblocblbcdcpbko_0/2:                                                                                        SQLite 3.x database, last written using SQLite version 3032001
./databases/https_wmn.hu_0/51:                                                                                                                            SQLite 3.x database, last written using SQLite version 3030001
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