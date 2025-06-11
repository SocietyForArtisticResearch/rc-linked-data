#!/bin/bash

# Define the script to run
SCRIPT=("parse_rc.py" 0 0 0 1 1 1)
#python3 parse_rc.py <debug> <download> <shot> <map> <force> <resume> [auth] [lookup]
    
# Run the script in the background
python3 "${SCRIPT[@]}" &

# Get the PID of the running script
PID=$!

# Wait a moment to ensure the process is running
sleep 1

# Apply CPU limit (25%) to the specific process
cpulimit -l 200 -p $PID &

# Wait for the script to finish
wait $PID



