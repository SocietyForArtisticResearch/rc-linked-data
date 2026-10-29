#!/bin/bash

# Log everything to a file per day (logs/run-v2-2026-10-29.log), instead of cron mailing it.
LOG_DIR=/home/casper/devel/rc-linked-data/logs
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run-v2-$(date +%F).log"
# Keep cron's original output as fd 3: anything written there is mailed by cron.
exec 3>&1
exec >> "$LOG_FILE" 2>&1
echo "=== run-v2 started $(date) ==="
# On any failing command, mail a short error report (the script itself keeps going).
trap 'status=$?
      echo "run-v2.sh: line $LINENO failed (exit $status): $BASH_COMMAND" >&3
      echo "Full log: $LOG_FILE, last lines:" >&3
      tail -n 20 "$LOG_FILE" >&3
      echo >&3' ERR
# Remove logs older than 30 days
find "$LOG_DIR" -name 'run-v2-*.log' -mtime +30 -delete

# This parses all new expositions, and takes screenshots. It also creates a index.json in each screenshot folder
bash /home/casper/devel/rc-linked-data/parsers/run2.sh     
echo "Parser is done."

# Merge the tool stats (how many video tools, how horizontal etc..)
cd /home/casper/devel/rc-linked-data/db
echo "Starting merging..."
/home/casper/devel/rc-linked-data/db/.venv/bin/python /home/casper/devel/rc-linked-data/db/merge_stats.py
echo "Merging is done."

# This currently creates the index of screenshots, we need to change this to use the new index.json instead.
echo "make the index json of the screenshots"
cd /mnt/screenshots/screenshots
/home/casper/.opam/default/bin/ocaml structure_extract.ml ./ > screenshots.json
cd /home/casper/devel/rc_data

echo "fetch a fresh internal_research.json"
rm internal_research.json
#wget keywords.sarconference2016.net/internal_research.json
wget map.rcdata.org/internal_research.json


echo "make a new enriched json file"
elm-cli run src/Main.elm

echo "copy to live app"
#cp enriched.json /var/www/html/rc-prisma/enriched.json
cp enriched.json /var/www/html/enriched.json
#we pre zip this big file, so we save some bandwidth
gzip -f -k -9 /var/www/html/enriched.json 


