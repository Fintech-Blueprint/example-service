# Vault OIDC Best Practices

This document outlines the best practices for using HashiCorp Vault with GitHub Actions OIDC authentication in our organization.

## Core Principles

### 1. Principle of Least Privilege

- **Repository-Specific Roles**: Create separate Vault roles for each repository instead of org-wide roles
```hcl
bound_claims = {
  "repository": "Fintech-Blueprint/specific-repo"
}
```

- **Branch Protection**: For sensitive repositories, bind roles to specific branches
```hcl
bound_claims = {
  "ref": "refs/heads/main",
  "repository": "Fintech-Blueprint/sensitive-repo"
}
```

- **Limited Policies**: Grant minimal required permissions in Vault policies
```hcl
# Good - specific path and capabilities
path "secret/data/ci/repo-specific/*" {
  capabilities = ["read"]
}

# Bad - too broad
path "secret/data/*" {
  capabilities = ["read", "list"]
}
```

### 2. Token Lifecycle Management

- Set appropriate TTLs for tokens:
  ```hcl
  token_ttl = "1h"
  token_max_ttl = "4h"
  ```

- Make tokens renewable but with limited renewal periods
  ```hcl
  token_bound_cidrs = ["0.0.0.0/0"]  # Restrict if possible
  token_explicit_max_ttl = "24h"
  ```

- Implement token revocation procedures for compromised credentials

### 3. Secure Claims Configuration

- Use strict bound_claims_type:
  ```hcl
  bound_claims_type = "glob"  # Use "string" when exact matches are needed
  ```

- Include multiple claims for stronger binding:
  ```hcl
  bound_claims = {
    "repository": "Fintech-Blueprint/*",
    "environment": "production",
    "job_workflow_ref": "*.github/workflows/release.yml@*"
  }
  ```

### 4. Secret Management

- Rotate KV secrets periodically:
  ```bash
  # Script this process
  vault kv put secret/ci/org_gh_token \
    org_gh_token=@new_token \
    rotation_date=$(date -u +"%Y-%m-%d")
  ```

- Use separate secret paths for different environments:
  ```
  secret/ci/production/tokens
  secret/ci/staging/tokens
  secret/ci/development/tokens
  ```

- Implement version control for secrets:
  ```bash
  vault kv metadata set secret/ci/org_gh_token \
    max_versions=5 \
    delete_version_after="30d"
  ```

### 5. Monitoring and Auditing

#### Audit Logging

Enable comprehensive audit logging:
```bash
vault audit enable file file_path=/var/log/vault/audit.log
```

Key events to monitor:
- OIDC authentication attempts
- Token creation and usage
- Policy violations
- Secret access patterns

#### Metrics Collection

Monitor Vault metrics:
- Authentication success/failure rates
- Token usage patterns
- Rate limiting hits
- Response times

### 6. Emergency Procedures

#### Manual Authentication Fallback

When OIDC authentication fails:

1. Use the Vault CLI for manual authentication:
   ```bash
   vault login -method=userpass
   ```

2. Debug OIDC token claims:
   ```bash
   vault token lookup ${TOKEN}
   ```

3. Verify role configuration:
   ```bash
   vault read auth/jwt/role/github-actions
   ```

#### Break Glass Procedures

Document emergency access procedures:

1. Access to root tokens (stored in secure hardware)
2. Alternative authentication methods
3. Contact information for Vault administrators
4. Incident response playbooks

## Implementation Guidelines

### Initial Setup

1. Start with restrictive policies and gradually add permissions as needed
2. Document all role and policy changes in version control
3. Use infrastructure as code for Vault configuration
4. Implement automated testing for auth workflows

### Continuous Improvement

1. Regular security reviews of role configurations
2. Update bound claims based on repository changes
3. Adjust token TTLs based on usage patterns
4. Refine policies based on audit logs

### Training and Documentation

1. Maintain up-to-date setup guides
2. Document troubleshooting procedures
3. Provide training for new team members
4. Keep security playbooks current

## Compliance and Governance

### Regular Reviews

- Conduct quarterly audits of:
  - Role configurations
  - Policy assignments
  - Secret usage patterns
  - Access logs

### Documentation Requirements

- All changes must be:
  - Documented in version control
  - Reviewed by security team
  - Tested in non-production
  - Approved by system owners
