# Policy for safe deletion of archive entries
# Allows deletion of archive entries but requires specific path patterns
# and includes safety measures like mandatory metadata checks

# Read capability is required to verify metadata before deletion
path "secret/data/example-service/+/archive-*" {
  capabilities = ["read", "delete"]
}

# Metadata operations to verify archive status
path "secret/metadata/example-service/+/archive-*" {
  capabilities = ["read", "delete"]
}

# List capability to identify archives
path "secret/metadata/example-service/+" {
  capabilities = ["list"]
}

# Deny write operations to prevent accidental overwrites
path "secret/data/example-service/+/archive-*" {
  capabilities = ["deny"]
  denied_parameters = {
    "*" = []
  }
}

# Required for audit logging of deletion operations
path "sys/audit-hash/*" {
  capabilities = ["read"]
}