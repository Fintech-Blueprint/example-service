#!/bin/bash
set -euo pipefail

# Rotate a Vault secret with zero-downtime
SECRET_PATH=$1
SECRET_KEY=${2:-"token"}
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# Store new version in Vault
vault kv put "$SECRET_PATH" "$SECRET_KEY"="$NEW_SECRET"

# Create evidence entry
jq -n \
    --arg timestamp "$TIMESTAMP" \
    --arg path "$SECRET_PATH" \
    --arg key "$SECRET_KEY" \
    --arg hash "$(echo -n "$NEW_SECRET" | sha256sum | awk '{print $1}')" \
    '{
        event: "secret_rotation",
        timestamp: $timestamp,
        path: $path,
        key: $key,
        hash: $hash
    }' > "secret_rotation_${TIMESTAMP}.json"

# Store in audit trail
../audit/store-evidence.sh "secret-rotation" "secret_rotation_${TIMESTAMP}.json"

# Clean up
rm "secret_rotation_${TIMESTAMP}.json"

echo "Secret rotated successfully. Evidence stored in audit trail."

# Validate under load
echo "Running load test to verify zero-downtime..."
cd ../load-tests
./run-tests.sh "$SERVICE_URL" "compliance"

echo "Secret rotation completed and validated."