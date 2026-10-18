#!/bin/bash
# Serve the campus model locally (no build step required).
PORT="${1:-8123}"
cd "$(dirname "$0")"
echo "PolyU Campus in Massing → http://localhost:$PORT"
python3 -m http.server "$PORT"
