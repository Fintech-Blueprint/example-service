# 🔒 Vault KV v2 Archival & Token Rotation Cheat Sheet

A quick reference guide for daily operations with the Vault KV v2 archival system and token rotation.

## 📋 Quick Reference

### 🌟 Environment Setup
```bash
# Core setup
export VAULT_ADDR="https://vault-cluster-public-vault-d81cdec2.2d1e9c46.z1.hashicorp.cloud:8200"
export VAULT_TOKEN="your-token"
export VAULT_NAMESPACE="admin"       # default: admin
export VAULT_MOUNT="secret"          # default KV v2 mount path

# Optional
export MAX_ARCHIVE_SIZE_MB=500      # Archive size limit
```

### 📦 Archive Operations
```bash
# Basic archival
./scripts/vault-archive.sh /path/to/archive.tar.gz session_log.md

# Dry-run mode
./scripts/vault-archive.sh --dry-run /path/to/archive.tar.gz
```

#### Metadata Structure
- \`sha256\`: Checksum
- \`location\`: Storage path
- \`archived_by\`: Operator
- \`archived_at\`: Timestamp
- \`size\`: Optional size in bytes

### 🔑 Token Management

#### Available Roles
| Role | Access | TTL | Purpose |
|------|--------|-----|---------|
| archive-uploader | create, read, list | 24h | Write archives |
| archive-reader | read, list | 48h | Verify metadata |
| archive-deleter | read, delete | 12h | Safe cleanup |
| dev-read-only | read (dev) | 7d | Dev audits |
| admin | full | 4h | Administration |

#### Token Commands
```bash
# Initial setup
./scripts/vault-rotate-token.sh --setup

# Manual rotation
./scripts/vault-rotate-token.sh

# Apply new token
source .vault-token-archive-uploader

# Force rotation
./scripts/vault-rotate-token.sh --force
```

### 🔄 GitHub Actions

#### Manual Trigger Steps
1. Actions tab
2. "Token Rotation"
3. "Run workflow"
4. Select role (optional)

### 🚨 Common Issues

#### Token Expired
```bash
./scripts/vault-rotate-token.sh --force
source .vault-token-archive-uploader
```

#### Connection Problems
```bash
env | grep VAULT_
vault status
```

#### Permission Errors
```bash
vault token lookup
vault token capabilities secret/example-service/
```

## 📝 Best Practices

### Token Safety
- Rotate frequently (daily/4-hourly)
- Use environment-specific tokens
- Verify after rotation
- Never share across environments

### Archive Safety
- Always dry-run first
- Verify checksums
- Check size limits
- Validate metadata
- Read-back verification

### Monitoring
- Watch expiry notifications
- Check rotation logs
- Review audit trails
- Monitor failed operations

## 🔍 Session Log Example
```markdown
## Archive Operation
- Vault path: secret/example-service/archive-name
- Written on: 2025-09-23T01:13:52Z
- By: operator
- Location: file:///path/to/archive.tar.gz
- SHA256: <checksum>
- Size: 42 MB
- Write verified: ✅
- GPG verified: ✅
```

## 📚 Related Documentation
- Full Setup: [ONBOARDING.md](./ONBOARDING.md)
- Deployment: [ROLLOUT.md](./ROLLOUT.md)
- Policy Templates: [../scripts/vault/policies/](../scripts/vault/policies/)
- Integration: [README.md](./README.md)