#!/bin/bash
set -euo pipefail

# Validate secret rotation logs for compliance
AUDIT_DIR="../audit"
YEAR=$(date +"%Y")
MONTH=$(date +"%m")
DAY=$(date +"%d")

# Check recent rotations
find "$AUDIT_DIR/$YEAR/$MONTH/$DAY/secret-rotation" -name "evidence_*.json" -type f | while read -r file; do
    # Verify signature
    if [[ ! -f "${file}.sig" ]]; then
        echo "ERROR: Missing signature for $file"
        exit 1
    fi
    
    cosign verify-blob \
        --key ~/.cosign/cosign.pub \
        --signature "${file}.sig" \
        "$file"
    
    # Check rotation event
    jq -e '.event == "secret_rotation"' "$file" > /dev/null || {
        echo "ERROR: Invalid rotation event in $file"
        exit 1
    }
    
    # Verify hash format
    jq -e '.hash | test("^[a-f0-9]{64}$")' "$file" > /dev/null || {
        echo "ERROR: Invalid hash format in $file"
        exit 1
    }
done

echo "Secret rotation logs validated successfully."