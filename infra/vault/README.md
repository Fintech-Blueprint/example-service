# Vault OIDC integration for GitHub Actions

This document explains how the repository integrates HashiCorp Vault with GitHub Actions using OIDC. It covers Vault configuration, secret management, workflow usage, repository setup, token rotation, and troubleshooting. Follow the steps carefully and avoid printing secrets in CI logs.

## Overview

GitHub Actions workflows in this repository now authenticate to Vault using OIDC and fetch CI secrets at runtime instead of relying on long-lived repository secrets. This reduces risk from leaked tokens and allows centralized secret rotation in Vault.

Branch/PR with changes: `ops/vault-oidc-integration` (see PR on the repository for the exact changes).

## Vault Configuration

These are the recommended steps to configure Vault for GitHub Actions OIDC.

1. Enable the OIDC auth method (if not already enabled):

```bash
# Use a Vault token with the required privileges and optionally set VAULT_NAMESPACE
export VAULT_ADDR="https://<your-vault-address>:8200"
export VAULT_TOKEN="<your-admin-token>"
export VAULT_NAMESPACE=admin # if using namespaces

vault auth enable oidc
```

2. Configure OIDC using the GitHub Actions token issuer:

```bash
vault write auth/oidc/config \
  oidc_discovery_url="https://token.actions.githubusercontent.com" \
  oidc_client_id="vault" \
  oidc_client_secret="<optional-client-secret-if-required>"
```

If your Vault distribution requires both client id and secret, provide the secret. Some managed instances may work using discovery only.

3. Create the `github-actions` role (example using the HTTP API or CLI payload):

Example JSON payload (HTTP API):

```json
{
  "bound_claims": {"repository": "Fintech-Blueprint/example-service"},
  "bound_audiences": ["vault"],
  "policies": ["github-actions"],
  "ttl": "1h",
  "user_claim": "sub",
  "allowed_redirect_uris": ["https://flow.idp.hashicorp.com/sso/oidc/callback"]
}
```

Write the role using the CLI (if your CLI supports map input) or the API:

```bash
# Using HTTP API (idempotent)
curl --header "X-Vault-Token: $VAULT_TOKEN" \
  --request PUT \
  --data '{"bound_claims":{"repository":"Fintech-Blueprint/example-service"},"bound_audiences":["vault"],"policies":["github-actions"],"ttl":"1h","user_claim":"sub","allowed_redirect_uris":["https://flow.idp.hashicorp.com/sso/oidc/callback"]}' \
  "$VAULT_ADDR/v1/auth/oidc/role/github-actions"
```

4. Add the Vault policy `github-actions` (example HCL):

```hcl
# infra/vault/github-actions.hcl
path "secret/data/ci/*" {
  capabilities = ["read"]
}
```

Apply the policy:

```bash
vault policy write github-actions infra/vault/github-actions.hcl
```

## Secrets Management

Store CI tokens in Vault KV v2 under `secret/ci/`:

```bash
# Example: write the org-level GitHub token
vault kv put secret/ci/org_gh_token value="<ORG_GH_TOKEN>"

# Example: write the Terraform API token
vault kv put secret/ci/tf_api_token value="<TF_API_TOKEN>"
```

Verify the keys (metadata listing):

```bash
vault kv list secret/ci
# Expected: org_gh_token, tf_api_token
```

Read a secret value locally if needed (avoid printing in CI logs):

```bash
vault kv get -field=value secret/ci/org_gh_token
```

## Workflow Usage

Workflows use `hashicorp/vault-action@v2` to perform an OIDC login and map Vault KV secrets to environment variables.

Example (high-level):

```yaml
- name: Login to Vault
  uses: hashicorp/vault-action@v2
  with:
    url: ${{ secrets.VAULT_ADDR }}
    method: oidc
    role: github-actions
    response_wrap: false
    env: |
      ORG_GH_TOKEN=secret/data/ci/org_gh_token#value
      TF_API_TOKEN=secret/data/ci/tf_api_token#value

- name: Use org token
  run: |
    # use $ORG_GH_TOKEN here (do not print it)
    echo "Will use org token in subsequent steps"
  env:
    ORG_GH_TOKEN: ${{ env.ORG_GH_TOKEN }}
```

Workflows intentionally map secrets to env vars `ORG_GH_TOKEN` and `TF_API_TOKEN`. The code in this repo's workflows was updated on branch `ops/vault-oidc-integration` to use these env variables instead of long-lived secrets.

## GitHub Repository Setup

Set the `VAULT_ADDR` repository secret so workflows know where to authenticate:

```bash
export VAULT_ADDR="https://<your-vault-address>:8200"
gh secret set VAULT_ADDR --body "$VAULT_ADDR" --repo Fintech-Blueprint/example-service
```

Remove old long-lived secrets from the repository (recommended):

```bash
gh secret delete ORG_GH_TOKEN --repo Fintech-Blueprint/example-service || true
gh secret delete TF_API_TOKEN --repo Fintech-Blueprint/example-service || true
```

## CI Token Rotation

To rotate CI tokens safely:

1. Prepare new tokens and write them to Vault KV paths (create new versions):

```bash
vault kv put secret/ci/org_gh_token value="<NEW_ORG_GH_TOKEN>"
vault kv put secret/ci/tf_api_token value="<NEW_TF_API_TOKEN>"
```

2. Trigger the `test-org-token.yml` workflow to validate the new tokens are used correctly.
3. Once validated, revoke or delete old tokens where appropriate.

## Troubleshooting

If the workflow fails to login to Vault via OIDC, check the following:

- Role bound_claims: ensure `repository` claim in the role matches the repo (e.g. `Fintech-Blueprint/example-service`).
- Token `sub` claim: inspect the token claims returned in the workflow logs (if present) to compare.
- Allowed redirect URIs on the role: must include `https://flow.idp.hashicorp.com/sso/oidc/callback`.
- Vault policy: ensure `github-actions` policy exists and grants `read` on `secret/data/ci/*`.
- VAULT_ADDR correctness: confirm workflows use the correct `VAULT_ADDR` repo secret.

Debugging tips:

- Add a step to dump the token subject (sub) in a safe manner (avoid printing tokens):
  - The Vault action may log claims when login fails — examine action logs.
- Use `vault read auth/oidc/role/github-actions` (with admin token) to confirm role configuration.

## Contact / Next Steps

If you'd like, Copilot can:

- Poll the running workflow and report completion and logs.
- Revoke any tokens you ask to be scrubbed from Vault or the repo.
- Add more strict policies or narrower secret paths for least privilege.

---

*Generated by Copilot-style automation: follow security best practices and avoid exposing secrets in CI logs.*
