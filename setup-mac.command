#!/bin/bash
#
# setup-mac.command — one-time setup to run Citation Checker as a Word add-in on macOS.
#
# Double-click this file in Finder (or run `bash setup-mac.command` in Terminal).
# It does the two things that make Word accept the add-in:
#
#   1. Creates and trusts an HTTPS certificate for https://localhost:8000
#      (Word task panes MUST be served over trusted HTTPS).
#   2. Copies manifest.xml into Word's hidden "sideload" folder so the add-in
#      appears on Word's Home ribbon. (On Mac there is no "Import" button —
#      this folder *is* how you install a developer add-in.)
#
# After this runs once, start the app any time with ./run.command (or
# `python3 backend/main.py`), then open Word and click the Citation Checker button.

set -u
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

CERT_DIR="$HOME/.office-addin-dev-certs"
CERT="$CERT_DIR/localhost.crt"
KEY="$CERT_DIR/localhost.key"
WEF_DIR="$HOME/Library/Containers/com.microsoft.Word/Data/Documents/wef"

echo ""
echo "  Citation Checker — Word add-in setup (macOS)"
echo "  ============================================"
echo ""

# ── 1. HTTPS certificate ──────────────────────────────────────────────────────
mkdir -p "$CERT_DIR"

if [ -f "$CERT" ] && [ -f "$KEY" ]; then
  echo "  [1/2] HTTPS certificate already present — reusing it."
else
  echo "  [1/2] Creating an HTTPS certificate for https://localhost:8000…"
  echo "        Using openssl (built into macOS)…"
  CONF="$(mktemp)"
  cat > "$CONF" <<'EOF'
[req]
distinguished_name = dn
x509_extensions    = v3
prompt             = no
[dn]
CN = localhost
[v3]
subjectAltName        = @alt
basicConstraints      = critical, CA:TRUE
keyUsage              = critical, digitalSignature, keyCertSign
extendedKeyUsage      = serverAuth
[alt]
DNS.1 = localhost
IP.1  = 127.0.0.1
EOF
  openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$KEY" -out "$CERT" -days 825 \
    -config "$CONF" -extensions v3 >/dev/null 2>&1
  rm -f "$CONF"
fi

# Trust the certificate in the SYSTEM keychain. Word's task pane runs in a
# sandbox that does NOT honour login-keychain trust, so this must be system-wide
# or the pane shows "isn't signed by a valid security certificate".
if security find-certificate -c localhost /Library/Keychains/System.keychain >/dev/null 2>&1; then
  echo "        Certificate already trusted system-wide."
else
  echo "        Trusting the certificate system-wide so Word's sandbox accepts it."
  echo "        You'll be asked for your Mac password — this is expected."
  if sudo security add-trusted-cert -d -r trustRoot \
       -k /Library/Keychains/System.keychain "$CERT"; then
    echo "        Trusted."
  else
    echo "        NOTE: could not auto-trust. Open Keychain Access, find 'localhost',"
    echo "        double-click it, expand Trust, set 'Always Trust', then reopen Word."
  fi
fi
echo ""

# ── 2. Sideload the manifest ──────────────────────────────────────────────────
echo "  [2/2] Installing the add-in into Word…"
mkdir -p "$WEF_DIR"
cp "$PROJECT_DIR/manifest.xml" "$WEF_DIR/citation-checker-manifest.xml"
echo "        Copied manifest to:"
echo "        $WEF_DIR"
echo ""

echo "  ✅ Setup complete."
echo ""
echo "  Next steps:"
echo "    1. Start the checker:   double-click run.command"
echo "                            (or run:  python3 backend/main.py )"
echo "    2. Quit Word completely (Cmd+Q) and reopen it."
echo "    3. On the Home tab, click  ‘Citation Checker’  to open the pane."
echo "    4. Paste your Gemini API key, then click ‘Scan & check this document’."
echo ""
read -n 1 -s -r -p "  Press any key to close this window."
echo ""
