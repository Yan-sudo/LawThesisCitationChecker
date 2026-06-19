#!/bin/bash
#
# run.command — start the Citation Checker server on macOS.
# Double-click in Finder, or run `bash run.command` in Terminal.
#
# Serves the task pane + citation-checking API at https://localhost:8000
# (HTTPS is used automatically once setup-mac.command has created the cert).
# Leave this window open while you use the add-in in Word; press Ctrl+C to stop.

cd "$(dirname "$0")/backend" || exit 1
PORT=8000

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found. Install it from https://www.python.org/downloads/"
  read -n 1 -s -r -p "Press any key to close."
  exit 1
fi

# If the port is already taken, work out whether it's our own server (already
# running — nothing to do) or some other program (needs freeing).
if command -v lsof >/dev/null 2>&1 && lsof -ti tcp:$PORT >/dev/null 2>&1; then
  if curl -sk --max-time 3 "https://localhost:$PORT/health" 2>/dev/null | grep -q '"ok"' \
     || curl -s  --max-time 3 "http://localhost:$PORT/health"  2>/dev/null | grep -q '"ok"'; then
    echo ""
    echo "  Citation Checker is already running at https://localhost:$PORT — you're all set."
    echo "  Switch to Word and click ‘Citation Checker’ on the Home tab."
    echo ""
    echo "  (To restart it fresh:  lsof -ti tcp:$PORT | xargs kill )"
    echo ""
    read -n 1 -s -r -p "  Press any key to close this window."
    echo ""
    exit 0
  else
    echo ""
    echo "  Port $PORT is in use by another program (not the checker)."
    echo "  Free it, then run this again:"
    echo "      lsof -ti tcp:$PORT | xargs kill"
    echo ""
    read -n 1 -s -r -p "  Press any key to close this window."
    echo ""
    exit 1
  fi
fi

echo ""
echo "  Starting Citation Checker…  (close this window or press Ctrl+C to stop)"
echo ""
python3 main.py "$@"
