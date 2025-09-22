# Copilot Guardrails for Workflows & CI/CD

This repo enforces strict workflow standards.
**Copilot must follow these rules when suggesting code.**

---

## 1. YAML Formatting Rules
- Always start workflow files with `---`.
- Maximum line length = 80 characters.
- Use block scalars (`>`) to wrap long `run:` commands.
- Do not use "truthy" shorthand. Always write:
  ```yaml
  branches:
    - "main"
  ```

## 2. Workflow File Structure

One workflow = one job type (lint, test, deploy, vault-auth, etc.).

Use matrix strategy for OS, Python versions, or test types:

```yaml
strategy:
  fail-fast: true
  matrix:
    python-version: ["3.9", "3.10", "3.11"]
    os: [ubuntu-latest]
```

Always use the latest action versions:
- actions/checkout@v4
- actions/setup-python@v5
- hashicorp/vault-action@v3

## 3. Variable Naming (do not invent new ones)

Valid variables are defined in workflow-vars.md.
Allowed prefixes:

- secrets. → Vault or GitHub secrets
- env. → environment variables
- matrix. → matrix entries

Examples:

${{ secrets.VAULT_ADDR }}
${{ env.CI_ENV }}
${{ matrix.python-version }}

## 4. Token & Secret Handling

- Never log raw tokens or secrets.
- Always check for token expiration and refresh before usage.
- Do not reuse expired tokens in refactors.

## 5. Lint & Validation

- All workflows must pass yamllint (max 80 chars).
- All workflows must pass actionlint.
- Pre-commit hooks will block commits if rules are broken.

## 6. Commit & PR Standards

Prefix commit messages with one of:
- fix:
- feat:
- chore:
- ci:
- refactor:

PRs must pass validate-workflows.yml before merge.

## 7. Prohibited Behaviors

- Do not create new variable names.
- Do not duplicate existing workflows.
- Do not inline secrets.
- Do not bypass matrix strategies.
