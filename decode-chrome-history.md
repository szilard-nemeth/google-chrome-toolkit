## Set env vars
```
CURR_TABS="/Users/szilardnemeth/Library/Application Support/Google/Chrome/Profile 1/Current Tabs"
CURR_SESSION="/Users/szilardnemeth/Library/Application Support/Google/Chrome/Profile 1/Current Session"
CHROMAGNON_REPO="$HOME/development/my-repos/Chromagnon"
```

## Retrieve current tabs + current session
Invoke Chromagnon
```
python $CHROMAGNON_REPO/chromagnonTab.py $CURR_TABS > /tmp/chromagnon-currenttabs
python $CHROMAGNON_REPO/chromagnonSession.py $CURR_SESSION > /tmp/chromagnon-currentsession
```

Invoke Chromagnon & parse URLs
```
python $CHROMAGNON_REPO/chromagnonTab.py $CURR_TABS | grep -v "newtab" | grep "Url:" | sed 's/.*.Url: \(.*\)/\1/' > /tmp/chromagnon-currenttabs-filtered
python $CHROMAGNON_REPO/chromagnonSession.py $CURR_SESSION | grep -v "newtab" | grep "Url:" | sed 's/.*.Url: \(.*\)/\1/' | sort | uniq > /tmp/chromagnon-currentsession-filtered
```

## Open all generates files with Sublime
```
find /tmp/ -iname "*chromagnon*" -print0 | xargs -0 subl
```