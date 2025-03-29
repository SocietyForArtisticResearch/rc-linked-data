#!/bin/bash

# Define the script to run
SCRIPT="rcData_API_live.py"

# Run the script in the background
python3 "$SCRIPT" &

# Get the PID of the running script
PID=$!

# Wait a moment to ensure the process is running
sleep 1

# Apply CPU limit (25%) to the specific process
cpulimit -l 25 -p $PID &

# Wait for the script to finish
wait $PID

