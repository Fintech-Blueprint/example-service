# admin policy
# Full KV management for the example-service path

# Full access to KV v2 secrets under example-service/
path "secret/data/example-service/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Full access to metadata
path "secret/metadata/example-service/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Allow policy and role management
path "sys/policies/acl/example-service-*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "auth/token/roles/example-service-*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Allow token creation
path "auth/token/create/example-service-*" {
  capabilities = ["create", "update"]
}