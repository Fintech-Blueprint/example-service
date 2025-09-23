Archive upload instructions

Do not run uploads unless you have the required credentials and permissions. The archive is currently at `secure/artifacts/secret-exposure-2025-09-23.tar.gz`.

Option A — Upload to S3 (recommended if you have an encrypted S3 bucket with restricted ACLs)
- Required: IAM user with PutObject permission on the target bucket and KMS decrypt/encrypt if using SSE-KMS.

Example:
```bash
# set variables
BUCKET=s3://company-secure-archives
KEY=example-service/secret-exposure-2025-09-23.tar.gz
aws s3 cp secure/artifacts/secret-exposure-2025-09-23.tar.gz "$BUCKET/$KEY" --acl bucket-owner-full-control
# verify
aws s3 ls "$BUCKET/$KEY"
```

Option B — Upload to HashiCorp Vault (Enterprise/OSS note: Vault is not a file storage; use a secure object store and store a pointer in Vault)
- Recommended: upload to secure object storage and store metadata + checksum in Vault kv2.

Example (store checksum in Vault kv2):
```bash
vault kv put secret/example-service/secret-exposure-2025-09-23 sha256="$(cat secure/artifacts/secret-exposure-2025-09-23.sha256)" location="s3://company-secure-archives/example-service/secret-exposure-2025-09-23.tar.gz" archived_by="<name>" archived_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

Option C — Manual transfer to compliance storage
- If you must transfer the tarball manually, use a secure channel (SCP to a hardened host, physically transfer on encrypted media) and verify checksum after transfer.

Verification after upload
- Recompute checksum on the remote side and confirm it matches `secure/artifacts/secret-exposure-2025-09-23.sha256`.
- Record custody: who uploaded, destination, timestamp, and retention policy.

Recordkeeping
- Add an entry in the compliance tracking system with archive location, checksum, uploader identity, and retention instructions.

If you provide the destination (S3 bucket path or Vault path) and confirm you want me to perform the upload, I can run it (you must provide credentials or give me a temporary role with permission). Otherwise I will leave these instructions and mark the upload prep todo as completed.

Vault uploader flow (admin created policy & token):
- Admin has created a policy `example-service-archive` and a short-lived token for the uploader. The uploader must export `VAULT_ADDR` and `VAULT_TOKEN` locally.

Uploader commands (run locally after exporting VAULT_ADDR & VAULT_TOKEN):
```bash
# Preferred: use vault CLI
vault kv put secret/example-service/secret-exposure-2025-09-23 \
	sha256="$(awk '{print $1}' secure/artifacts/secret-exposure-2025-09-23.sha256)" \
	location="file://$(pwd)/secure/artifacts/secret-exposure-2025-09-23.tar.gz" \
	archived_by="$(whoami)" \
	archived_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# If vault CLI not available, curl approach (requires VAULT_ADDR & VAULT_TOKEN in env):
sha="$(awk '{print $1}' secure/artifacts/secret-exposure-2025-09-23.sha256)"; loc="file://$(pwd)/secure/artifacts/secret-exposure-2025-09-23.tar.gz"; who="$(whoami)"; at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
curl --silent --show-error --header "X-Vault-Token: $VAULT_TOKEN" --request POST "$VAULT_ADDR/v1/secret/data/example-service/secret-exposure-2025-09-23" -d "{\"data\":{\"sha256\":\"$sha\",\"location\":\"$loc\",\"archived_by\":\"$who\",\"archived_at\":\"$at\"}}"
```

After uploading, verify with:
```bash
vault kv get -format=json secret/example-service/secret-exposure-2025-09-23
# or
curl --silent --show-error --header "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/data/example-service/secret-exposure-2025-09-23" | jq .
```

Record custody by appending the verification output to `session_log.md` and updating `upload_instructions.md` with the Vault KV path and timestamp.
