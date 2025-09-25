#!/bin/bash
set -euo pipefail

# Package a new Golden Goose release
VERSION=$1
RELEASE_DIR="releases/$VERSION"

# Create release directory structure
mkdir -p "$RELEASE_DIR"/{sbom,compliance,dashboards,signatures}

# Collect SBOM
cyclonedx-py generate -r -o "$RELEASE_DIR/sbom/sbom.json"

# Copy compliance evidence (references only)
jq -n \
  --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg version "$VERSION" \
  '{timestamp: $timestamp, version: $version, references: {"audit": "audit/'"$VERSION"'"}}' \
  > "$RELEASE_DIR/compliance/evidence.json"

# Copy Grafana dashboards
cp -r ../grafana-dashboards/* "$RELEASE_DIR/dashboards/"

# Create manifest
jq -n \
  --arg version "$VERSION" \
  --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  '{version: $version, timestamp: $timestamp, components: ["sbom", "compliance", "dashboards"]}' \
  > "$RELEASE_DIR/manifest.json"

# Sign release
cosign sign-blob \
  --key ~/.cosign/cosign.key \
  "$RELEASE_DIR/manifest.json" \
  > "$RELEASE_DIR/signatures/manifest.sig"

echo "Release $VERSION packaged successfully"