# archive-reader policy
# Read-only access for verification and audit

# Allow reading KV v2 secrets under example-service/
path "secret/data/example-service/*" {
  capabilities = ["read"]
}

# Allow listing metadata
path "secret/metadata/example-service/*" {
  capabilities = ["list", "read"]
}

# Deny other operations
path "secret/*" {
  capabilities = ["deny"]
}