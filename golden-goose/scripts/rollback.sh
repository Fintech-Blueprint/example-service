#!/bin/bash
set -euo pipefail

# Handle rollback to a specific Golden Goose release
VERSION=$1
RELEASE_DIR="releases/$VERSION"

# Verify release first
./verify.sh "$VERSION"

# Record rollback in audit log
echo "{\"event\":\"rollback\",\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"version\":\"$VERSION\"}" >> ../audit/rollbacks.log

# Restore dashboards
cp -r "$RELEASE_DIR/dashboards/"* ../grafana-dashboards/

# Update current version pointer
echo "$VERSION" > current_version

echo "Rolled back to version $VERSION successfully"