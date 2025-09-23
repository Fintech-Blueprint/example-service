# Vault KV v2 Archival Protocol

This script implements a secure, repeatable protocol for archiving metadata into HashiCorp Vault KV v2. It includes safety checks, duplicate detection, and optional GPG verification.

## Features

- ✅ **Safety Checks**
  - Vault connectivity verification
  - Archive size validation
  - Duplicate SHA256 detection
  - Optional GPG signature verification

- 🔒 **Security**
  - Namespace-aware operations
  - Write verification
  - Session logging for audit
  - Clear error reporting

- 📝 **Metadata Storage**
  - SHA256 checksum
  - File location
  - Archive timestamp
  - Archival operator
  - Archive size

## Prerequisites

- Vault KV v2 backend mounted at `secret/`
- Token with appropriate permissions (create, read, list)
- `jq` command-line tool installed
- Optional: GPG for signature verification

## Environment Variables

```bash
# Required
export VAULT_ADDR="https://your-vault-server:8200"
export VAULT_TOKEN="your-token"

# Optional
export VAULT_NAMESPACE="admin"        # Default: admin
export VAULT_MOUNT="secret"          # Default: secret
export MAX_ARCHIVE_SIZE_MB="500"     # Default: 500
```

## Usage

### Basic Usage
```bash
# Regular archive operation
./vault-archive.sh /path/to/archive.tar.gz [session_log.md]

# Dry-run mode (simulate only)
./vault-archive.sh --dry-run /path/to/archive.tar.gz [session_log.md]
```

### With GPG Verification
```bash
# If archive.tar.gz.sig exists, signature will be verified
./vault-archive.sh /path/to/archive.tar.gz
```

## Safety Features

1. **Pre-flight Checks**
   - Validates environment variables
   - Checks Vault connectivity
   - Verifies archive file existence
   - Warns on large archives

2. **Duplicate Detection**
   - Computes SHA256 of archive
   - Checks for existing archives with same SHA
   - Prompts for confirmation if duplicate found

3. **GPG Verification**
   - Automatically detects .sig files
   - Verifies archive integrity if signature present
   - Fails if verification unsuccessful

4. **Write Verification**
   - Reads back written metadata
   - Confirms data integrity
   - Updates session log with verification status

## Session Log Format

Each archive operation adds an entry to the session log:

```markdown
Archive custody record:
- Vault path: secret/example-service/archive-name (namespace: admin)
- Metadata written on: 2025-09-23T01:13:52Z
- Written by: operator
- Location: file:///path/to/archive.tar.gz
- SHA256: 0ea1968262751d1aed2c75b9059a89bc52f57031bff7fa5b96c9883f34e05191
- Archive size: 42 MB
- Write verified: Yes (read-back successful)
- GPG verified: Yes (if applicable)
```

## Error Handling

The script fails gracefully with clear error messages for:
- Missing environment variables
- Invalid Vault token
- Network connectivity issues
- File access problems
- Duplicate archives (with override option)
- Failed GPG verification
- Write verification failures

## Token Rotation

The `vault-rotate-token.sh` script provides automated token rotation:

```bash
# First-time setup (creates policy and role)
./vault-rotate-token.sh --setup

# Environment variables for token rotation
export VAULT_ADDR="https://your-vault-server:8200"
export VAULT_NAMESPACE="admin"
export VAULT_TOKEN="admin-token"      # needs policy creation rights
export TOKEN_TTL="8h"                # optional, default 8h
export TOKEN_ROLE="archive-uploader" # optional
export TOKEN_POLICY="example-service-archive" # optional

# Rotate token
./vault-rotate-token.sh

# Use new token
source .vault-token-archive-uploader
```

Features:
- Creates required policy and token role
- Generates new token with appropriate permissions
- Verifies new token functionality
- Saves token environment to a protected file
- Supports custom TTL and role names

The rotation script will:
1. Create the policy if needed (first time setup)
2. Create a token role with the specified TTL
3. Generate a new token bound to that role
4. Verify the token works
5. Save credentials to a protected file

Best practice: rotate tokens:
- On a regular schedule (e.g., daily)
- After completing major operations
- If compromise is suspected
- When team members change

## Best Practices

1. Always use `--dry-run` first to validate operations
2. Keep session logs for audit purposes
3. Use GPG signatures for sensitive archives
4. Rotate Vault tokens regularly using `vault-rotate-token.sh`
5. Monitor archive sizes and implement retention policies
6. Use separate tokens for different environments/purposes
7. Never share tokens across teams or projects

## Support

For issues or enhancements:
- Open an issue in the repository
- Contact the security team
- Review session logs for troubleshooting