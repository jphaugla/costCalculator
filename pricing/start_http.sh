#!/bin/bash
# start_http.sh - Serve the current directory over HTTP with CORS support.
# Allows specifying a custom port. Defaults to 8000 if no port is provided.

# Get the directory of this script and change to it.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Get the port from the first argument, default to 8000
PORT=${1:-8000}

echo "Serving directory $DIR on http://localhost:$PORT"

# Run the Python server in the background and redirect logs
nohup python3 CORS_server.py --port "$PORT" > http_ec2.log 2>&1 &

