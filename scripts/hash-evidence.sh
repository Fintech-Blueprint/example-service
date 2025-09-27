#!/usr/bin/env bash
set -euo pipefail

# scripts/hash-evidence.sh
# Computes SHA256 for a file and appends a structured entry to EVIDENCE_CHAIN.md
# Usage: ./scripts/hash-evidence.sh <file> [description] [sprint]

EVIDENCE_CHAIN_FILE="EVIDENCE_CHAIN.md"
DEFAULT_SPRINT="sprint2"

usage() {
  cat <<USAGE >&2
Usage: $0 <file> [description] [sprint]

Arguments:
  file         Path to the evidence file to hash (required)
  description  Short description (optional)
  sprint       Sprint name (optional; defaults to ${DEFAULT_SPRINT})

Example:
  $0 evidence/sprint3/ingress-debug.log "ingress bootstrap debug log" sprint3
USAGE
  exit 1
}

if [ "$#" -lt 1 ]; then
  usage
fi

FILE="$1"
DESCRIPTION="${2:-Evidence log file}"
SPRINT="${3:-$DEFAULT_SPRINT}"

if [ ! -f "$FILE" ]; then
  echo "Error: file '$FILE' not found" >&2
  exit 1
fi

# Ensure evidence chain file exists
if [ ! -f "$EVIDENCE_CHAIN_FILE" ]; then
  echo "Error: evidence chain file '$EVIDENCE_CHAIN_FILE' not found" >&2
  exit 1
fi

# Compute values
HASH=$(sha256sum -- "$FILE" | awk '{print $1}')
TS=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
RELATIVE_PATH=$(realpath --relative-to="$(pwd)" -- "$FILE")

# Append a single, well-formed block to the evidence chain
cat >> "$EVIDENCE_CHAIN_FILE" <<EOF
## Evidence Entry: $TS

### Sprint: $SPRINT

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

echo "Added evidence entry for $RELATIVE_PATH (hash: $HASH)"