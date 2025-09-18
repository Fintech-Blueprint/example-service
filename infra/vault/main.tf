// Terraform stub for Vault provisioning (HCP Vault or self-hosted)
// This is a placeholder. A Vault admin or infra engineer must populate provider
// credentials and backend values. Copilot can generate the detailed TF configs
// but will not apply them without infrastructure credentials.

terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
  }
}

provider "vault" {
  # address = var.vault_address
  # token   = var.vault_token
}

// Example: enable KV v2 at secret/
resource "vault_mount" "secret" {
  path = "secret"
  type = "kv-v2"
}

output "vault_address" {
  value = var.vault_address
  description = "Address of the provisioned Vault instance"
  sensitive = true
}
