path "secret/data/ci/*" {
  capabilities = ["read"]
}

path "secret/metadata/ci/*" {
  capabilities = ["list", "read"]
}