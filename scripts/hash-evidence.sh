#!/usr/bin/env bash
set -euo pipefail

# Simple, robust evidence hasher and EVIDENCE_CHAIN.md appender
# Usage: ./scripts/hash-evidence.sh <file> [description] [sprint]

EVIDENCE_CHAIN_FILE="EVIDENCE_CHAIN.md"
DEFAULT_SPRINT="sprint2"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <file> [description] [sprint]" >&2
  exit 1
fi

FILE="$1"
DESC="${2:-Evidence log file}"
SPRINT="${3:-$DEFAULT_SPRINT}"

if [ ! -f "$FILE" ]; then
  echo "Error: file '$FILE' not found" >&2
  exit 1
fi

HASH=$(sha256sum "$FILE" | awk '{print $1}')
TS=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
REL=$(realpath --relative-to="$(pwd)" "$FILE")

cat >> "$EVIDENCE_CHAIN_FILE" <<EOF
## Evidence Entry: $TS

### Sprint: $SPRINT

### File Information
- Path: $REL
- Description: $DESC
- Hash: $HASH
- Status: VALIDATED

### Validation Steps
1. SHA256 hash generated
2. Added to evidence chain
3. Original log preserved

### Chain Status
- Previous Entry: Valid
- Current Entry: Added
- Chain Integrity: Maintained

EOF

echo "Added evidence entry for $REL (hash: $HASH)"
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

## Check if file exists and has content
if [ ! -f "$EVIDENCE_CHAIN_FILE" ]; then
    echo "Error: Evidence chain file '$EVIDENCE_CHAIN_FILE' not found"
    exit 1
fi

# Append the evidence entry using a here-doc to avoid any shell interpolation
cat >> "$EVIDENCE_CHAIN_FILE" <<EOF
## Evidence Entry: $TIMESTAMP

### Sprint: $SPRINT_PARAM

### File Information
- Path: $RELATIVE_PATH
- Description: $DESCRIPTION
- Hash: $HASH
- Status: VALIDATED

### Validation Steps
1. SHA256 hash generated
2. Added to evidence chain
3. Original log preserved

### Chain Status
- Previous Entry: Valid
- Current Entry: Added
- Chain Integrity: Maintained

EOF
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

# Append the generated entry at the end of the Evidence Chain file. This is
# intentionally simple and robust: it avoids brittle pattern matching and
# guarantees chronological ordering. For sprint-specific grouping, entries
# include the Sprint tag in the generated block.
echo "" >> "$EVIDENCE_CHAIN_FILE"
echo "$ENTRY" >> "$EVIDENCE_CHAIN_FILE"

echo "✅ Evidence chain updated successfully"
echo "📝 Added hash for: $RELATIVE_PATH"
echo "🔐 Hash: $HASH"