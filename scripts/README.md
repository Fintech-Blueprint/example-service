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

## Best Practices

1. Always use `--dry-run` first to validate operations
2. Keep session logs for audit purposes
3. Use GPG signatures for sensitive archives
4. Rotate Vault tokens regularly
5. Monitor archive sizes and implement retention policies

## Support

For issues or enhancements:
- Open an issue in the repository
- Contact the security team
- Review session logs for troubleshooting