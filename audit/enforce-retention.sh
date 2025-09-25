#!/bin/bash
set -euo pipefail

# Enforce retention policy by archiving old evidence
RETENTION_YEARS=3
CURRENT_YEAR=$(date +"%Y")
ARCHIVE_BEFORE=$((CURRENT_YEAR - RETENTION_YEARS))

# Find directories older than retention period
find . -maxdepth 1 -type d -name "[0-9][0-9][0-9][0-9]" | while read -r year_dir; do
    year=$(basename "$year_dir")
    if [[ "$year" -lt "$ARCHIVE_BEFORE" ]]; then
        # Create archive
        archive_name="evidence_${year}.tar.gz"
        tar czf "$archive_name" "$year_dir"
        
        # Sign archive
        cosign sign-blob \
            --key ~/.cosign/cosign.key \
            "$archive_name" \
            > "${archive_name}.sig"
        
        # Move to cold storage
        aws s3 cp "$archive_name" "s3://audit-archive/${archive_name}"
        aws s3 cp "${archive_name}.sig" "s3://audit-archive/${archive_name}.sig"
        
        # Clean up local files
        rm -f "$archive_name" "${archive_name}.sig"
        rm -rf "$year_dir"
        
        echo "Archived and removed evidence from $year"
    fi
done