#!/bin/bash
#
# setup-mac.command — set up Citation Checker as a Word add-in on macOS.
#
# Double-click this file in Finder (or run `bash setup-mac.command` in Terminal).
# It does the three things that make Word accept and show the add-in:
#
#   1. Creates a proper CA→localhost HTTPS certificate and trusts the CA
#      system-wide. Word's task pane runs sandboxed and is stricter than Safari:
#      it wants a CA-signed certificate trusted in the System keychain.
#   2. Clears Word's add-in cache, so a previously-cached "certificate blocked"
#      error doesn't stick around.
#   3. Copies manifest.xml into Word's hidden sideload folder so the add-in
#      appears on the Home ribbon. (On Mac there is no "Import" button —
#      this folder *is* how you install a developer add-in.)
#
# Re-running this is safe; pass --force-cert to rebuild the certificate.

set -u
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

CERT_DIR="$HOME/.office-addin-dev-certs"
CERT="$CERT_DIR/localhost.crt"      # fullchain (leaf + CA) the server presents
KEY="$CERT_DIR/localhost.key"       # leaf private key
CA_CERT="$CERT_DIR/lexcheck-rootCA.crt"
CA_KEY="$CERT_DIR/lexcheck-rootCA.key"
CA_NAME="LexCheck Local Dev CA"
WEF_DIR="$HOME/Library/Containers/com.microsoft.Word/Data/Documents/wef"

echo ""
echo "  Citation Checker — Word add-in setup (macOS)"
echo "  ============================================"
echo ""

mkdir -p "$CERT_DIR"

# ── 1. HTTPS certificate (CA → localhost leaf) ────────────────────────────────
need_cert=1
if [ -f "$CERT" ] && [ -f "$KEY" ] && [ -f "$CA_CERT" ] && [ "${1:-}" != "--force-cert" ]; then
  need_cert=0
fi

if [ "$need_cert" = "0" ]; then
  echo "  [1/3] HTTPS certificate already present — reusing it."
else
  echo "  [1/3] Creating a CA-signed HTTPS certificate for https://localhost:8000…"

  CA_CNF="$(mktemp)"; LEAF_CNF="$(mktemp)"
  cat > "$CA_CNF" <<EOF
[req]
distinguished_name = dn
x509_extensions    = v3_ca
prompt             = no
[dn]
CN = $CA_NAME
[v3_ca]
basicConstraints = critical, CA:true
keyUsage         = critical, keyCertSign, cRLSign
EOF
  cat > "$LEAF_CNF" <<'EOF'
[req]
distinguished_name = dn
prompt             = no
[dn]
CN = localhost
[v3_leaf]
subjectAltName   = DNS:localhost, IP:127.0.0.1
basicConstraints = critical, CA:false
keyUsage         = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
EOF

  # Root CA
  openssl req -x509 -new -nodes -newkey rsa:2048 \
    -keyout "$CA_KEY" -out "$CA_CERT" -days 825 \
    -config "$CA_CNF" -extensions v3_ca >/dev/null 2>&1
  # Leaf signed by the CA
  openssl req -new -nodes -newkey rsa:2048 \
    -keyout "$KEY" -out "$CERT_DIR/localhost.csr" \
    -config "$LEAF_CNF" >/dev/null 2>&1
  openssl x509 -req -in "$CERT_DIR/localhost.csr" \
    -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
    -out "$CERT_DIR/localhost-leaf.crt" -days 825 \
    -extfile "$LEAF_CNF" -extensions v3_leaf >/dev/null 2>&1
  # Server presents leaf + CA so the chain is complete
  cat "$CERT_DIR/localhost-leaf.crt" "$CA_CERT" > "$CERT"
  rm -f "$CA_CNF" "$LEAF_CNF" "$CERT_DIR/localhost.csr"
  echo "        Certificate created."
fi

# Trust the CA in the SYSTEM keychain (sandboxed Word ignores login-keychain trust)
if security find-certificate -c "$CA_NAME" /Library/Keychains/System.keychain >/dev/null 2>&1 \
   && [ "${1:-}" != "--force-cert" ]; then
  echo "        Certificate authority already trusted system-wide."
else
  echo "        Trusting the certificate system-wide so Word's sandbox accepts it."
  echo "        You'll be asked for your Mac password — this is expected."
  if sudo security add-trusted-cert -d -r trustRoot \
       -k /Library/Keychains/System.keychain "$CA_CERT"; then
    echo "        Trusted."
  else
    echo "        NOTE: could not auto-trust. Open Keychain Access, find"
    echo "        '$CA_NAME', set it to 'Always Trust', then reopen Word."
  fi
fi
echo ""

# ── 2. Clear Word's add-in cache ──────────────────────────────────────────────
echo "  [2/3] Clearing Word's add-in cache…"
osascript -e 'quit app "Microsoft Word"' >/dev/null 2>&1
sleep 1
rm -rf "$HOME/Library/Containers/com.microsoft.Word/Data/Library/Caches/"* 2>/dev/null
rm -rf "$HOME/Library/Containers/com.microsoft.Word/Data/Library/WebKit/"*  2>/dev/null
rm -rf "$HOME/Library/Containers/com.Microsoft.OsfWebHost/Data/"*           2>/dev/null
echo "        Done."
echo ""

# ── 3. Sideload the manifest ──────────────────────────────────────────────────
echo "  [3/3] Installing the add-in into Word…"
mkdir -p "$WEF_DIR"
cp "$PROJECT_DIR/manifest.xml" "$WEF_DIR/citation-checker-manifest.xml"
echo "        Installed."
echo ""

echo "  ✅ Setup complete."
echo ""
echo "  Next steps:"
echo "    1. Start the checker:   double-click run.command"
echo "                            (or run:  python3 backend/main.py )"
echo "    2. Open Word (it was closed to clear the cache)."
echo "    3. On the Home tab, click  ‘Citation Checker’  to open the pane."
echo "    4. Paste your Gemini API key, then click ‘Scan & check this document’."
echo ""
read -n 1 -s -r -p "  Press any key to close this window."
echo ""
