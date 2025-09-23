#!/usr/bin/env bash
# Vault token rotation script for archive operations
# Version: 1.0.0
set -euo pipefail

# ==============================
# Configuration
# ==============================
VAULT_ADDR="${VAULT_ADDR:?VAULT_ADDR must be set}"
VAULT_NAMESPACE="${VAULT_NAMESPACE:-admin}"
VAULT_TOKEN="${VAULT_TOKEN:?VAULT_TOKEN must be set}"
TOKEN_TTL="${TOKEN_TTL:-8h}"
TOKEN_ROLE="${TOKEN_ROLE:-archive-uploader}"
TOKEN_POLICY="${TOKEN_POLICY:-example-service-archive}"

# ==============================
# Functions
# ==============================
check_vault_connection() {
    echo "🔍 Checking Vault connection..."
    if ! vault token lookup -namespace="$VAULT_NAMESPACE" >/dev/null 2>&1; then
        echo "❌ Cannot connect to Vault or invalid token"
        return 1
    fi
}

create_policy() {
    local policy_name="$1"
    echo "📝 Creating Vault policy: $policy_name"
    
    vault policy write -namespace="$VAULT_NAMESPACE" "$policy_name" - <<EOF
# Allow managing KV v2 secrets under example-service/
path "secret/data/example-service/*" {
  capabilities = ["create", "read", "update", "list"]
}

# Allow checking KV v2 metadata
path "secret/metadata/example-service/*" {
  capabilities = ["list", "read"]
}
EOF
}

create_token_role() {
    local role_name="$1"
    echo "🔑 Creating token role: $role_name"
    
    vault write -namespace="$VAULT_NAMESPACE" auth/token/roles/"$role_name" \
        allowed_policies="$TOKEN_POLICY" \
        period="$TOKEN_TTL" \
        renewable=true \
        token_ttl="$TOKEN_TTL"
}

rotate_token() {
    echo "🔄 Rotating token..."
    
    # Create new token
    local new_token_info
    new_token_info=$(vault token create -namespace="$VAULT_NAMESPACE" \
        -role="$TOKEN_ROLE" \
        -format=json)
    
    if [[ -z "$new_token_info" ]]; then
        echo "❌ Failed to create new token"
        return 1
    fi
    
    local new_token
    new_token=$(echo "$new_token_info" | jq -r '.auth.client_token')
    
    # Verify new token works
    echo "✅ Verifying new token..."
    VAULT_TOKEN="$new_token" vault token lookup -namespace="$VAULT_NAMESPACE" >/dev/null
    
    # Output token info (in production, send to secure channel)
    echo "New token created:"
    echo "$new_token_info" | jq '
        .auth | {
            token: .client_token,
            accessor: .accessor,
            ttl: .lease_duration,
            renewable: .renewable,
            policies: .token_policies
        }
    '
    
    # Create token environment file
    local token_file=".vault-token-${TOKEN_ROLE}"
    {
        echo "export VAULT_ADDR='$VAULT_ADDR'"
        echo "export VAULT_NAMESPACE='$VAULT_NAMESPACE'"
        echo "export VAULT_TOKEN='$new_token'"
    } > "$token_file"
    chmod 600 "$token_file"
    
    echo "✅ Token environment saved to: $token_file"
    echo "To use: source $token_file"
}

# ==============================
# Main
# ==============================
main() {
    check_vault_connection || exit 1
    
    # Setup if needed
    if [[ "${1:-}" == "--setup" ]]; then
        create_policy "$TOKEN_POLICY"
        create_token_role "$TOKEN_ROLE"
        echo "✅ Token infrastructure setup complete"
        exit 0
    fi
    
    # Rotate token
    rotate_token
}

main "$@"