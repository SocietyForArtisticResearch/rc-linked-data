#!/bin/bash

bash /home/casper/devel/rc-linked-data/parsers/run2.sh     
echo "Parser is done."

cd /home/casper/devel/rc-linked-data/db
echo "Starting merging..."
python3 /home/casper/devel/rc-linked-data/db/merge_stats.py
echo "Merging is done."

echo "make the index json of the screenshots"
cd /mnt/screenshots/screenshots
/home/casper/.opam/default/bin/ocaml structure_extract.ml ./ > screenshots.json
cd /home/casper/devel/rc_data

echo "make a new enriched json file"
elm-cli run src/Main.elm

echo "copy to live app"
#cp enriched.json /var/www/html/rc-prisma/enriched.json
cp enriched.json /var/www/html/enriched.json



