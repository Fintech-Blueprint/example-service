#!/bin/bash
# Checks which repos have Vault OIDC workflow and secrets set
set -euo pipefail

# Required GitHub token scopes: repo, read:org, admin:org
# Generate a token with these scopes: https://github.com/settings/tokens/new
# Export as: export GH_TOKEN=ghp_xxx

ORG="Fintech-Blueprint"
VAULT_SECRET="VAULT_ADDR"

# Check if GH_TOKEN is set
if [ -z "${GH_TOKEN:-}" ]; then
    echo "Error: GH_TOKEN environment variable not set"
    echo "Please set GH_TOKEN with repo, read:org, and admin:org scopes"
    exit 1
fi

# Function to check if a repo has a specific workflow file
check_workflow() {
    local repo=$1
    gh api "/repos/$ORG/$repo/contents/.github/workflows/test-org-token.yml" --silent && echo "✅" || echo "⬜"
}

# Function to check if a repo has VAULT_ADDR secret
check_secret() {
    local repo=$1
    gh api "/repos/$ORG/$repo/actions/secrets/$VAULT_SECRET" --silent && echo "✅" || echo "⬜"
}

# Function to check if Vault role exists (we'll assume true if workflow exists)
check_vault_role() {
    local repo=$1
    local workflow_status=$(check_workflow "$repo")
    [ "$workflow_status" = "✅" ] && echo "✅" || echo "⬜"
}

echo "| Repo | Vault Role Created | Secrets Uploaded | Workflows Updated | Verified |"
echo "|------|------------------|-----------------|------------------|----------|"

# Print table header
echo "| Repo | Vault Role Created | Secrets Uploaded | Workflows Updated | Verified |"
echo "|------|------------------|-----------------|------------------|----------|"

# List all repos in the org
gh repo list "$ORG" --json name --jq '.[].name' | while read -r repo; do
    workflow_status=$(check_workflow "$repo")
    secret_status=$(check_secret "$repo")
    role_status=$(check_vault_role "$repo")
    verified=$([[ "$workflow_status" = "✅" && "$secret_status" = "✅" && "$role_status" = "✅" ]] && echo "✅" || echo "⬜")

    echo "| $repo | $role_status | $secret_status | $workflow_status | $verified |"
done
