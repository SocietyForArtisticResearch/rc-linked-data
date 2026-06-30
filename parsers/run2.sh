#!/bin/bash
cd /home/casper/devel/rc-linked-data/parsers || exit 1
source venv/bin/activate

# Define the script to run
# python3 parse_rc.py [--debug] [--download] [--shot] [--maps] [--force] [--resume]
#                      [--auth] [--research-folder PATH] [--screenshots-root PATH]
#                      [--lookup URL]


SCRIPT=(parse_rc.py --shot --screenshots-root /mnt/screenshots/screenshots --maps)

    
# Run the script in the background
python3 "${SCRIPT[@]}" &

# Get the PID of the running script
PID=$!

# Wait a moment to ensure the process is running
sleep 1

# Apply CPU limit (200%) to the specific process
cpulimit -l 200 -p $PID &

# Wait for the script to finish
wait $PID





