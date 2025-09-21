#!/bin/bash
# Script to setup Vault in Docker and configure JWT auth

# Cleanup
docker stop vault-dev || true
docker rm vault-dev || true

# Run Vault in Docker
docker run --cap-add=IPC_LOCK -d \
    --name vault-dev \
    -p 8200:8200 \
    -e VAULT_DEV_ROOT_TOKEN_ID=dev-token \
    -e VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200 \
    hashicorp/vault:latest \
    server -dev

# Wait for Vault to start
sleep 5

# Export Vault environment variables
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=dev-token

# Enable and configure JWT auth
vault auth enable jwt

vault write auth/jwt/config \
    bound_issuer="https://token.actions.githubusercontent.com" \
    jwks_url="https://token.actions.githubusercontent.com/.well-known/jwks"

# Create and apply the GitHub Actions policy
vault policy write github-actions-policy github-actions-policy.hcl

vault write auth/jwt/role/github-actions \
    role_type="jwt" \
    bound_audiences="https://github.com/Fintech-Blueprint" \
    bound_issuer="https://token.actions.githubusercontent.com" \
    bound_subject="repo:Fintech-Blueprint/example-service:ref:refs/heads/main" \
    token_policies="github-actions-policy" \
    user_claim="workflow" \
    ttl="10m"

# Verify configuration
vault read auth/jwt/config