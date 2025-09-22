# Vault OIDC Rollout Plan

## Overview
This document outlines the plan to adopt Vault OIDC authentication for GitHub Actions across all repositories in the Fintech-Blueprint organization.

## Current Adoption Status
Below is the current status of Vault OIDC adoption across our repositories. This table is automatically updated using the `check_adoption.sh` script.

### Current Status (Updated: 2025-09-21)
| Repo | Vault Role Created | Secrets Uploaded | Workflows Updated | Verified |
|------|------------------|-----------------|------------------|----------|
| example-service | ✅ | ⬜ | ✅ | ⬜ |
| api-gateway | ⬜ | ⬜ | ⬜ | ⬜ |
| db-manager | ⬜ | ⬜ | ⬜ | ⬜ |

### Platform Services
| Repo | Vault Role Created | Secrets Uploaded | Workflows Updated | Verified |
|------|------------------|-----------------|------------------|----------|
| platform-libs | ⬜ | ⬜ | ⬜ | ⬜ |
| design-system | ⬜ | ⬜ | ⬜ | ⬜ |
| catalog | ⬜ | ⬜ | ⬜ | ⬜ |

### Infrastructure
| Repo | Vault Role Created | Secrets Uploaded | Workflows Updated | Verified |
|------|------------------|-----------------|------------------|----------|
| infra | ⬜ | ⬜ | ⬜ | ⬜ |
| staging-env | ⬜ | ⬜ | ⬜ | ⬜ |
| contracts | ⬜ | ⬜ | ⬜ | ⬜ |

## Rollout Timeline

### Week 1: Pilot Phase (Current)
- ✅ `example-service`: Complete Vault OIDC integration
- ✅ Document setup process and best practices
- ✅ Create reusable workflow templates

### Week 2-3: Core Services
- [ ] `api-gateway`: Migrate to Vault OIDC
- [ ] `db-manager`: Migrate to Vault OIDC
- [ ] Verify CI/CD pipeline stability
- [ ] Document any service-specific configurations

### Week 4: Platform Services
- [ ] `platform-libs`: Migrate to Vault OIDC
- [ ] `design-system`: Migrate to Vault OIDC
- [ ] `catalog`: Migrate to Vault OIDC
- [ ] Update shared CI/CD templates

### Week 5: Infrastructure & Support
- [ ] `infra`: Migrate to Vault OIDC
- [ ] `staging-env`: Migrate to Vault OIDC
- [ ] `contracts`: Migrate to Vault OIDC
- [ ] Implement monitoring for Vault usage

## Prerequisites for Each Repo

Before starting migration:
1. Repository admin access
2. `VAULT_ADDR` secret configured
3. Workflows using GitHub secrets identified
4. Team notified of migration timeline

## Verification Steps

For each repository:
1. Run test workflow with Vault OIDC
2. Verify secrets are retrieved successfully
3. Check Vault audit logs for access
4. Remove old GitHub secrets
5. Update repository documentation

## Rollback Plan

If issues occur:
1. Revert workflow to use GitHub secrets
2. Revoke Vault tokens if compromised
3. Document incident and resolution
4. Update rollout plan if needed

## Monitoring

Track adoption progress:
```bash
# Update adoption status
./infra/vault/check_adoption.sh

# View Vault audit logs
vault audit list
```

## Support

For assistance during rollout:
- Slack: #vault-oidc-support
- Documentation: infra/vault/README.md
- Escalation: DevOps team
