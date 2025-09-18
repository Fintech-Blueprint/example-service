#!/usr/bin/env bash
# Helper to perform OIDC login from Codespaces / dev shell to Vault.
# This script assumes `gh` CLI is available and configured.
# It exchanges a GitHub OIDC token for Vault and writes VAULT_TOKEN to stdout.

set -euo pipefail

if [ -z "${VAULT_ADDR:-}" ]; then
  echo "VAULT_ADDR is not set. Please export VAULT_ADDR or set repo var VAULT_ADDR."
  exit 1
fi

# Request an ID token from gh CLI for the current repo
ID_TOKEN=$(gh auth token --hostname api.github.com 2>/dev/null || true)
if [ -z "$ID_TOKEN" ]; then
  echo "Could not obtain GH token from gh CLI. Ensure gh is logged in and supports id-token issuance."
  exit 1
fi

# Note: This is a convenience stub. Real implementation should use gh oidc-token or other flows
# to request an OIDC token scoped for the repository. The exact command depends on gh version.

echo "This script is a placeholder. Use the Vault action in CI for OIDC auth or request an OIDC token via 'gh auth' features.'"
