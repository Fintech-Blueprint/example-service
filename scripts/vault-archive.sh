#!/usr/bin/env bash
set -euo pipefail

# =============================
# Vault KV v2 Archive Protocol
# =============================

# Configuration and validation
VAULT_ADDR="${VAULT_ADDR:-https://vault-cluster-public-vault-d81cdec2.2d1e9c46.z1.hashicorp.cloud:8200}"
VAULT_NAMESPACE="${VAULT_NAMESPACE:-admin}"
VAULT_TOKEN="${VAULT_TOKEN:?Error: VAULT_TOKEN must be set}"
KV_MOUNT="secret"

# Validate inputs
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 /path/to/archive.tar.gz [session_log.md]"
    exit 1
fi

ARCHIVE_PATH="$1"
SESSION_LOG="${2:-session_log.md}"

if [[ ! -f "$ARCHIVE_PATH" ]]; then
    echo "❌ Archive not found: $ARCHIVE_PATH"
    exit 1
fi

if [[ ! -f "$SESSION_LOG" ]]; then
    echo "⚠️  Creating new session log: $SESSION_LOG"
    touch "$SESSION_LOG"
fi

echo "🔒 Vault KV v2 Archive Protocol"
echo "==============================="
echo "VAULT_ADDR: $VAULT_ADDR"
echo "VAULT_NAMESPACE: $VAULT_NAMESPACE"
echo "Archive: $ARCHIVE_PATH"
echo "Session log: $SESSION_LOG"
echo "---------------------------------------"

# Step 1: Prepare metadata values
SHA=$(sha256sum "$ARCHIVE_PATH" | awk '{print $1}')
LOC="file://$ARCHIVE_PATH"
BY=$(whoami)
AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SECRET_PATH="example-service/$(basename "$ARCHIVE_PATH" .tar.gz)"

echo "📝 Metadata prepared:"
echo "sha256: $SHA"
echo "location: $LOC"
echo "archived_by: $BY"
echo "archived_at: $AT"
echo "secret_path: $SECRET_PATH"
echo "---------------------------------------"

# Step 2: Write to Vault KV v2
echo "📤 Writing to Vault..."
if ! vault kv put -namespace="$VAULT_NAMESPACE" \
    -mount="$KV_MOUNT" \
    "$SECRET_PATH" \
    sha256="$SHA" \
    location="$LOC" \
    archived_by="$BY" \
    archived_at="$AT"; then
    echo "❌ Failed to write to Vault"
    exit 1
fi

# Step 3: Verify the write
echo "🔍 Verifying write..."
VERIFY=$(vault kv get -namespace="$VAULT_NAMESPACE" \
    -mount="$KV_MOUNT" \
    -format=json \
    "$SECRET_PATH")

if [[ -z "$VERIFY" ]]; then
    echo "❌ Failed to verify write"
    exit 1
fi

echo "✅ Write verified. Stored metadata:"
echo "$VERIFY" | jq '.data.data'

# Step 4: Append to session log
echo "📋 Updating session log..."
{
    echo
    echo "Archive custody record:"
    echo "- Vault path: $KV_MOUNT/$SECRET_PATH (namespace: $VAULT_NAMESPACE)"
    echo "- Metadata written on: $AT"
    echo "- Written by: $BY"
    echo "- Location: $LOC"
    echo "- SHA256: $SHA"
    echo "- Write verified: Yes (read-back successful)"
} >> "$SESSION_LOG"

echo "✅ Protocol completed successfully"
echo "- Metadata stored in Vault at: $KV_MOUNT/$SECRET_PATH"
echo "- Custody record added to: $SESSION_LOG"