#!/usr/bin/env bash
# Script to check token expiry and notify
set -euo pipefail

TOKEN_DIR="${TOKEN_DIR:-$HOME/.vault-tokens}"
NOTIFY_BEFORE="${NOTIFY_BEFORE:-1h}"

check_token() {
    local role="$1"
    local token_file="$TOKEN_DIR/.vault-token-${role}"
    
    if [[ ! -f "$token_file" ]]; then
        echo "⚠️ No token file found for $role"
        return 1
    }
    
    # Source the token file
    # shellcheck disable=SC1090
    source "$token_file"
    
    # Check token TTL
    local ttl
    ttl=$(vault token lookup -format=json | jq -r '.data.ttl')
    local hours=$((ttl / 3600))
    
    if [[ $ttl -lt 3600 ]]; then
        echo "🚨 Token for $role expires in less than 1 hour!"
        return 1
    elif [[ $hours -lt 4 ]]; then
        echo "⚠️ Token for $role expires in $hours hours"
        return 1
    fi
    
    echo "✅ Token for $role valid for $hours hours"
    return 0
}

# Check all role tokens
for role in archive-uploader archive-reader admin; do
    if ! check_token "$role"; then
        # Create GitHub issue for expiring token
        if [[ -n "${GITHUB_TOKEN:-}" ]]; then
            gh issue create \
                --title "🔑 Vault token expiring soon: $role" \
                --body "Token for role $role is expiring soon. Please rotate the token using:

\`\`\`bash
./scripts/vault-rotate-token.sh rotate $role
\`\`\`

Or trigger the rotation workflow manually in GitHub Actions." \
                --label "security"
        fi
    fi
done