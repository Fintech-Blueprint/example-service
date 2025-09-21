# Example Service (Golden Template)

This is the golden template service for the Fintech-Blueprint organization.
Every new microservice should be cloned from this repository.

## Secure Token Management with Vault OIDC (New! 🔐)

This repository uses HashiCorp Vault with OIDC authentication for secure GitHub token management. This means you **do not need to create classic Personal Access Tokens (PATs)** for CI/CD operations.

### 🤖 AI-Friendly Overview

The system works like this:

1. GitHub Actions generates a special OIDC token that proves "I am a workflow running in repo X"
2. Vault verifies this proof and, if valid, provides a GitHub token
3. Your workflow can use this token for GitHub operations

Benefits:
- No manual token creation needed
- Tokens are short-lived and automatic
- Centralized security management
- Full audit trail of token usage

### 🔐 For New Developers

When you want to run workflows that need GitHub access:

1. You DON'T need to:
   - Create a classic PAT
   - Store tokens in GitHub Secrets
   - Manage token rotation

2. You DO need to:
   - Ensure your workflow has `permissions.id-token: write`
   - Use the vault-action to get tokens:
   ```yaml
   - uses: hashicorp/vault-action@v2
     with:
       url: ${{ secrets.VAULT_ADDR }}
       method: jwt
       jwtGithubAudience: "https://github.com/Fintech-Blueprint"
       role: github-actions
       namespace: admin
       path: jwt
       secrets: |
         secret/data/ci/org_gh_token org_gh_token
   ```

### 🛠️ For DevOps/SRE

Key infrastructure components:
1. Vault JWT auth method configured for GitHub OIDC
2. Role bindings using repository and ref claims
3. KV store for GitHub tokens with granular access

For details on infrastructure setup, see the DevOps documentation.

### 🔍 Debugging Token Access

If you encounter token issues:

1. Check the workflow has proper permissions:
```yaml
permissions:
  id-token: write
  contents: read
```

2. Verify OIDC token claims:
```bash
curl -H "Authorization: Bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
     "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=https://github.com/Fintech-Blueprint" | \
     jq -r .value | cut -d. -f2 | base64 -d | jq .
```

3. Test Vault access:
```bash
vault write -field=token auth/jwt/login role=github-actions jwt=$ACTIONS_ID_TOKEN
```

## Vault OIDC Setup

### Pre-requisites

Before setting up Vault OIDC authentication:

1. HashiCorp Vault cluster (HCP Vault or self-hosted)
2. GitHub repository with Actions enabled
3. Admin rights on both Vault and GitHub repository
4. `vault` CLI installed locally

### Vault Role Creation

1. Enable JWT auth method:
```bash
vault auth enable -path=jwt jwt
```

2. Configure JWT auth with GitHub OIDC:
```bash
vault write auth/jwt/config \
  oidc_discovery_url="https://token.actions.githubusercontent.com" \
  bound_issuer="https://token.actions.githubusercontent.com"
```

3. Create a role for GitHub Actions:
```bash
vault write auth/jwt/role/github-actions \
  role_type="jwt" \
  bound_audiences="https://github.com/Fintech-Blueprint" \
  bound_claims_type="glob" \
  bound_claims='{"repository": "Fintech-Blueprint/example-service"}' \
  user_claim="repository" \
  token_policies="github-actions" \
  token_ttl="1h" \
  token_max_ttl="4h"
```

4. Create policy for GitHub token access:
```hcl
# github-actions-policy.hcl
path "secret/data/ci/org_gh_token" {
  capabilities = ["read"]
}
```

```bash
vault policy write github-actions github-actions-policy.hcl
```

### GitHub Repository Setup

1. Configure repository secret:
```bash
gh secret set VAULT_ADDR --body="https://your-vault-cluster.vault.com"
```

2. Remove any old PAT tokens or GitHub secrets that are no longer needed
```bash
gh secret list  # Review existing secrets
gh secret remove OLD_TOKEN_SECRET  # Remove if found
```

### Workflow Usage

Minimal workflow example:
```yaml
name: Example Workflow
on: [push]

permissions:
  id-token: write
  contents: read

jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: hashicorp/vault-action@v2
        with:
          url: ${{ secrets.VAULT_ADDR }}
          method: jwt
          jwtGithubAudience: "https://github.com/Fintech-Blueprint"
          role: github-actions
          namespace: admin
          path: jwt
          secrets: |
            secret/data/ci/org_gh_token org_gh_token
```

### Troubleshooting

Common issues and solutions:

1. OIDC Login Failures
   - Verify role bound_claims match repository name exactly
   - Check VAULT_ADDR is correct and accessible
   - Ensure workflow has id-token: write permission

2. Claims Mismatch
   - Run token debug step to view actual claims
   - Update role bound_claims if needed
   - Check audience matches configuration

3. Redirect URI Issues
   - Verify OIDC discovery URL is correct
   - Check Vault is accessible from GitHub Actions
   - Confirm no proxy/firewall blocking OIDC endpoints

4. Token Permission Errors
   - Review policy capabilities
   - Check secret path matches exactly
   - Verify token TTL hasn't expired

## Architecture
- Hexagonal structure:
  - src/domain → business rules (pure logic, no dependencies)
  - src/application → use cases, API entrypoints (FastAPI here)
  - src/infrastructure → DB, queues, external systems
  - src/adapters → bridges between infra and domain

## Running Locally
```bash
pip install -r requirements.txt
uvicorn src.application.main:app --reload
```

Check: http://localhost:8000/healthz

## Running Tests
```
pytest
```

## Docker
```
docker build -t example-service .
docker run -p 8000:8000 example-service
```

## CI/CD

Pull Requests: lint + tests + SAST + SBOM + sign

Main branch: builds a Docker image

Future: staging deployment (Kubernetes)

## How to Create a New Service

Duplicate this repo.

Replace example-service with your service name.

Implement your domain logic under src/domain/.

Expose new APIs under src/application/.

Submit PR → CI/CD enforces gates.

## AI Onboarding & Org Token Guide

This repository includes automation and AI-driven generation workflows. To let a new AI session (or another automation agent) continue work, follow these steps.

### Important Update on Token Management

**Note**: The previous instructions about creating classic PATs have been superseded by our Vault OIDC integration. You no longer need to manually create tokens. The system automatically handles token management through Vault.

For AI agents and automation:
1. Use the provided Vault integration in workflows
2. Token management is automatic - no manual steps needed
3. Full audit trail is available in Vault logs

The old instructions below are kept for reference but are no longer the recommended approach:

1. Create an organization access token (short-lived recommended):

  - Go to GitHub Settings → Developer settings → Personal access tokens.
  - Create a token with `repo` and `workflow` scopes (and `admin:org` if you need org-level discovery).
  - Store the token securely. In this workspace we use an ephemeral file path for CI: `/tmp/installation.token`.

2. Provide the token to the environment where the AI runs:

  - Locally: `export GITHUB_TOKEN=ghp_...` or write to `/tmp/installation.token` and ensure file permissions are secure.
  - In CI: add the token as a repository secret and reference it via the workflow.

3. Quick start for a new AI session to explore the org and repo:

  - Ensure the token is available at `/tmp/installation.token` or as `GITHUB_TOKEN` env var.
  - From the workspace root run the common checks:

```bash
python3 - <<'PY'
import requests,os
TOKEN=open('/tmp/installation.token').read().strip() if os.path.exists('/tmp/installation.token') else os.environ.get('GITHUB_TOKEN')
headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json'}
owner='Fintech-Blueprint'; repo='example-service'
print(requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers).json())
PY
```

4. How the AI should continue work (recommended sequence):

  - Validate open PRs and required checks.
  - Run `validate-specs.yml` and `auto-generate.yml` for new specs.
  - When generating code, always run `flake8` and `pytest` locally before creating PRs.

5. Security & governance notes:

  - Do not store long-lived tokens in the repo. Use short-lived tokens or GitHub App installations.
  - The AI must honor `.copilot-instructions.md` for workflow generation rules and the Spec-to-System policies.

6. Contact & audit

  - Generated runs deposit reports under `reports/` and `audit-reports/` in the repository and as GitHub Actions artifacts.
  - If a run fails Compliance checks, the AI must create an issue and tag the spec owner; do not attempt silent fixes.

With these steps, a new AI session can pick up the repository, discover specs, run generation, and open PRs while following governance and traceability rules.
