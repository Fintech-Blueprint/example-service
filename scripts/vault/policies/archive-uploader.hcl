# archive-uploader policy
# Write-only access for archiving metadata

# Allow writing KV v2 secrets under example-service/
path "secret/data/example-service/*" {
  capabilities = ["create", "update"]
}

# Allow listing metadata for duplicate detection
path "secret/metadata/example-service/*" {
  capabilities = ["list", "read"]
}

# Deny other operations
path "secret/*" {
  capabilities = ["deny"]
}