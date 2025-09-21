# Vault & Codespace Admin Onboarding

This document walks a replacement Codespace admin (CEO) through the exact steps to reproduce the Vault/GitHub setup used by this repo so CI workflows can authenticate to Vault via GitHub Actions OIDC.

Security note
- The commands below require Vault admin-level token privileges. Only run them in a secure terminal.
- Tokens and secrets must be stored in a secrets manager (GitHub Secrets, environment variable vault, or a secure vault). Do NOT check them into source control.

Prerequisites
- Install `vault` CLI v1.11+ and `gh` CLI v2.0+ and `jq`.
- Vault address and an admin token (temporary or long-lived) with ability to manage auth methods, roles, and policies.
- Access to the repository and permission to create or update GitHub Actions repository secrets.

Variables you will use (replace values):
- VAULT_ADDR: https://vault-cluster-public-vault-d81cdec2.2d1e9c46.z1.hashicorp.cloud:8200
- VAULT_NAMESPACE: admin (optional; used in HCP Vault)
- VAULT_ADMIN_TOKEN: <paste-admin-token-here>
- REPO: Fintech-Blueprint/example-service

Step 1 — Set up local environment
```bash
export VAULT_ADDR="https://vault-cluster-public-vault-d81cdec2.2d1e9c46.z1.hashicorp.cloud:8200"
export VAULT_NAMESPACE=admin
export VAULT_TOKEN="<VAULT_ADMIN_TOKEN>"
```

Step 2 — Enable JWT auth method (if not already enabled)
```bash
vault auth list | grep jwt || vault auth enable jwt

# Configure discovery + default role
vault write auth/jwt/config \
  oidc_discovery_url="https://token.actions.githubusercontent.com" \
  bound_issuer="https://token.actions.githubusercontent.com" \
  default_role="ci-github-actions"
```

Step 3 — Create the `ci-github-actions` role
Choose a bound_subject pattern that matches the `sub` (subject) claim that GitHub emits for your workflow. Typical formats:
- repo:{org}/{repo}:ref:refs/heads/{branch}
- repo:{org}/{repo}:environment:{env}

A broad pattern example (accepts refs/heads/*):
```bash
vault write auth/jwt/role/ci-github-actions \
  role_type="jwt" \
  bound_audiences="vault" \
  user_claim="actor" \
  bound_claims_type="string" \
  bound_subject="repo:Fintech-Blueprint/example-service:ref:refs/heads/*" \
  token_policies="ci-github-actions"
```

Step 4 — Create policy used by the role
```bash
vault policy write ci-github-actions - <<'EOF'
# Allow reading CI secrets
path "secret/data/ci/*" {
  capabilities = ["read"]
}
EOF
```

Step 5 — Add required CI secrets to GitHub
(Repository or organization secrets; repository-level is enough here.)
```bash
# In your local shell with gh logged in:
gh secret set VAULT_ADDR --body "$VAULT_ADDR"
# The workflows use Vault OIDC to fetch secrets; no repository token is required for runtime.
# If you want to use a short-lived bootstrap token, store it securely.
```

Step 6 — (Optional) Add a test secret
```bash
vault kv put secret/ci/org_gh_token value="<placeholder-or-real-token>"
```

Step 7 — Verify the role and policy
```bash
vault read auth/jwt/role/ci-github-actions
vault policy read ci-github-actions
```

Step 8 — Re-run the workflow and inspect OIDC token debug output
- We added debugging steps to `ci.yml` that print the token claims. Watch the `lint` job logs for the output of `Debug OIDC token (lint)`.
- Confirm the `sub` claim in the token matches the Vault role's `bound_subject`.

Troubleshooting: common errors
- role "ci-github-actions" could not be found: Role not created in the configured namespace. Create it (see Step 3).
- error validating token: invalid subject (sub) claim: The token sub doesn't match the role's bound_subject. Either broaden the role or adjust bound_subject to match the observed `sub`.
- permission denied when calling `vault auth list` or `vault write`: the VAULT_TOKEN lacks privileges. Use an admin token.

Security & rotation
- Use Vault leases and short TTLs where possible.
- Rotate admin tokens and avoid long-lived tokens in environment variables. Use an admin session to create roles/policies then revoke.
- Store any bootstrap tokens in the GitHub Organization secrets (or HashiCorp Vault) rather than repository code.

Minimal CEO checklist (quick):
1. Install `vault`, `gh`, `jq`.
2. Export `VAULT_ADDR`, `VAULT_NAMESPACE`, and `VAULT_TOKEN`.
3. Run Steps 2–4 above to create JWT auth, role, and policy.
4. Confirm secret paths and run the workflow.