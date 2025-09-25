#!/bin/bash
set -euo pipefail

# Verify a Golden Goose release package
VERSION=$1
RELEASE_DIR="releases/$VERSION"

# Check required files
required_files=(
  "manifest.json"
  "signatures/manifest.sig"
  "sbom/sbom.json"
  "compliance/evidence.json"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$RELEASE_DIR/$file" ]]; then
    echo "Error: Missing required file $file"
    exit 1
  fi
done

# Verify manifest signature
cosign verify-blob \
  --key ~/.cosign/cosign.pub \
  --signature "$RELEASE_DIR/signatures/manifest.sig" \
  "$RELEASE_DIR/manifest.json"

# Verify SBOM
cyclonedx-py verify "$RELEASE_DIR/sbom/sbom.json"

# Verify evidence references
jq -e '.references.audit' "$RELEASE_DIR/compliance/evidence.json" > /dev/null

echo "Release $VERSION verified successfully"