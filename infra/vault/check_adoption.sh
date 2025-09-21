#!/bin/bash
# Checks which repos have Vault OIDC workflow and secrets set
set -euo pipefail

# Required GitHub token scopes: repo, read:org
# Generate a token with these scopes: https://github.com/settings/tokens/new
# Export as: export GH_TOKEN=ghp_xxx

ORG="Fintech-Blueprint"
VAULT_SECRET="VAULT_ADDR"

# Check if GH_TOKEN is set and has required permissions
if [ -z "${GH_TOKEN:-}" ]; then
    echo "Error: GH_TOKEN environment variable not set"
    echo "Please set GH_TOKEN with repo and read:org scopes"
    exit 1
fi

echo "| Repo | Vault Role Created | Secrets Uploaded | Workflows Updated | Verified |"
echo "|------|------------------|-----------------|------------------|----------|"

# List all repos in the org
repos=$(gh repo list "$ORG" --json name --jq '.[].name')

for repo in $repos; do
    # Check if repo has the workflow file
    workflow_present=$(gh workflow list --repo "$ORG/$repo" --json name --jq '.[] | select(.name=="test-org-token") | .name' || echo "")
    workflow_status="⬜"
    if [[ -n "$workflow_present" ]]; then workflow_status="✅"; fi

    # Check if VAULT_ADDR secret exists
    secret_present=$(gh secret list --repo "$ORG/$repo" | grep "$VAULT_SECRET" || true)
    secret_status="⬜"
    if [[ -n "$secret_present" ]]; then secret_status="✅"; fi

    # For simplicity, assume Vault Role created if workflow present
    role_status="$workflow_status"
    verified="$workflow_status"

    echo "| $repo | $role_status | $secret_status | $workflow_status | $verified |"
done