#!/bin/bash
# run_server.sh - Serve the current directory over HTTP on port 8000.
# Ensure that ec2_pricing.csv is in the same directory as this script.

# Get the directory of this script and change to it.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Serving directory $DIR on http://localhost:8000"
nohup python CORS_server.py > http_ec2.log 2>&1 &
