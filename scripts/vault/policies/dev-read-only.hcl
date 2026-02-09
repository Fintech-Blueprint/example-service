# Policy for read-only access to development environment archives
# Provides safe read-only access for development team audits and reviews

# Allow read-only access to development environment archives
path "secret/data/example-service/dev/*" {
  capabilities = ["read"]
}

# Allow listing of development environment paths
path "secret/metadata/example-service/dev/*" {
  capabilities = ["list", "read"]
}

# Deny any write/delete operations
path "secret/data/example-service/dev/*" {
  capabilities = ["deny"]
  denied_parameters = {
    "*" = []
  }
}

# Allow reading audit logs for development environment
path "sys/audit/*/hash" {
  capabilities = ["read"]
}

# Deny access to production and staging environments
path "secret/data/example-service/prod/*" {
  capabilities = ["deny"]
}

path "secret/data/example-service/staging/*" {
  capabilities = ["deny"]
}