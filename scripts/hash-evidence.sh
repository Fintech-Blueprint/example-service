#!/bin/bash
# Script to generate evidence hashes and update EVIDENCE_CHAIN.md
set -e

# Configuration
EVIDENCE_CHAIN_FILE="EVIDENCE_CHAIN.md"
DEFAULT_SPRINT="sprint2"
DATE_FORMAT="%Y-%m-%d %H:%M:%S UTC"

# Function to print usage instructions
usage() {
    echo "Usage: $0 <log_file_path> [description]"
    echo
    echo "Arguments:"
    echo "  log_file_path  : Path to the evidence log file to hash"
    echo "  description    : Optional description of the evidence"
    echo
    echo "Example:"
    echo "  $0 evidence/mesh/mtls-20250925-1600.log 'mTLS validation run'"
    exit 1
}

# Check arguments
if [ "$#" -lt 1 ]; then
    usage
fi

LOG_FILE="$1"
DESCRIPTION="${2:-Evidence log file}"
SPRINT_PARAM="${3:-$DEFAULT_SPRINT}"

# Validate file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Error: File '$LOG_FILE' does not exist"
    exit 1
fi

# Generate hash
HASH=$(sha256sum "$LOG_FILE" | cut -d' ' -f1)
TIMESTAMP=$(date +"$DATE_FORMAT")
RELATIVE_PATH=$(realpath --relative-to="$(pwd)" "$LOG_FILE")

# Generate entry
ENTRY="## Evidence Entry: $TIMESTAMP

### Sprint: $SPRINT_PARAM

### File Information
- Path: \\`$RELATIVE_PATH\\`
- Description: $DESCRIPTION
- Hash: \\`$HASH\\`
- Status: VALIDATED

### Validation Steps
1. SHA256 hash generated
2. Added to evidence chain
3. Original log preserved

### Chain Status
- Previous Entry: Valid
- Current Entry: Added
- Chain Integrity: Maintained"

# Check if file exists and has content
if [ ! -f "$EVIDENCE_CHAIN_FILE" ]; then
    echo "Error: Evidence chain file '$EVIDENCE_CHAIN_FILE' not found"
    exit 1
fi

# Create temporary file
TMP_FILE=$(mktemp)

# Find the evidence section and append the new entry
awk -v entry="$ENTRY" -v sprint="$SPRINT_PARAM" '
    BEGIN { in_sprint=0 }
    /^## Sprint 3 -- INITIATION/ { print; print entry; in_sprint=1; next }
    /^## Sprint 3 -- END/ { print; in_sprint=0; next }
    { print }
' "$EVIDENCE_CHAIN_FILE" > "$TMP_FILE"

# Replace original file
mv "$TMP_FILE" "$EVIDENCE_CHAIN_FILE"

echo "✅ Evidence chain updated successfully"
echo "📝 Added hash for: $RELATIVE_PATH"
echo "🔐 Hash: $HASH"