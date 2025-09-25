#!/bin/bash
set -euo pipefail

# Store compliance evidence with immutable hash chain
EVIDENCE_TYPE=$1
EVIDENCE_FILE=$2
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
YEAR=$(date -u +"%Y")
MONTH=$(date -u +"%m")
DAY=$(date -u +"%d")

# Create directory structure
TARGET_DIR="$YEAR/$MONTH/$DAY/$EVIDENCE_TYPE"
mkdir -p "$TARGET_DIR"

# Calculate hash of previous entry if it exists
PREV_HASH="0000000000000000000000000000000000000000"
if [[ -f "$TARGET_DIR/latest.json" ]]; then
    PREV_HASH=$(sha256sum "$TARGET_DIR/latest.json" | awk '{print $1}')
fi

# Create new evidence entry with hash chain
jq -n \
    --arg timestamp "$TIMESTAMP" \
    --arg type "$EVIDENCE_TYPE" \
    --arg prev_hash "$PREV_HASH" \
    --slurpfile evidence "$EVIDENCE_FILE" \
    '{
        timestamp: $timestamp,
        type: $type,
        previous_hash: $prev_hash,
        evidence: $evidence[0]
    }' > "$TARGET_DIR/evidence_${TIMESTAMP}.json"

# Update latest pointer
cp "$TARGET_DIR/evidence_${TIMESTAMP}.json" "$TARGET_DIR/latest.json"

# Sign evidence
cosign sign-blob \
    --key ~/.cosign/cosign.key \
    "$TARGET_DIR/evidence_${TIMESTAMP}.json" \
    > "$TARGET_DIR/evidence_${TIMESTAMP}.sig"

echo "Evidence stored at: $TARGET_DIR/evidence_${TIMESTAMP}.json"