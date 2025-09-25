#!/bin/bash
set -euo pipefail

# Verify evidence hash chain integrity
YEAR=$1
MONTH=$2
DAY=$3
EVIDENCE_TYPE=$4

TARGET_DIR="$YEAR/$MONTH/$DAY/$EVIDENCE_TYPE"

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: No evidence found for $YEAR-$MONTH-$DAY $EVIDENCE_TYPE"
    exit 1
fi

# Sort files by timestamp
readarray -t evidence_files < <(find "$TARGET_DIR" -name "evidence_*.json" | sort)

prev_hash="0000000000000000000000000000000000000000"
for file in "${evidence_files[@]}"; do
    # Verify file hash matches stored previous_hash
    current_prev_hash=$(jq -r .previous_hash "$file")
    if [[ "$current_prev_hash" != "$prev_hash" ]]; then
        echo "Error: Hash chain broken at $file"
        echo "Expected previous hash: $prev_hash"
        echo "Found previous hash: $current_prev_hash"
        exit 1
    fi
    
    # Verify signature
    sig_file="${file%.json}.sig"
    if [[ ! -f "$sig_file" ]]; then
        echo "Error: Missing signature for $file"
        exit 1
    fi
    
    cosign verify-blob \
        --key ~/.cosign/cosign.pub \
        --signature "$sig_file" \
        "$file"
    
    # Update prev_hash for next iteration
    prev_hash=$(sha256sum "$file" | awk '{print $1}')
done

echo "Evidence chain verified successfully for $YEAR-$MONTH-$DAY $EVIDENCE_TYPE"