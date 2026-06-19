#!/bin/bash
#
# run.command — start the Citation Checker server on macOS.
# Double-click in Finder, or run `bash run.command` in Terminal.
#
# Serves the task pane + citation-checking API at https://localhost:8000
# (HTTPS is used automatically once setup-mac.command has created the cert).
# Leave this window open while you use the add-in in Word; press Ctrl+C to stop.

cd "$(dirname "$0")/backend" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found. Install it from https://www.python.org/downloads/"
  read -n 1 -s -r -p "Press any key to close."
  exit 1
fi

echo ""
echo "  Starting Citation Checker…  (close this window or press Ctrl+C to stop)"
echo ""
python3 main.py "$@"
