# ROTATION.md

This document provides steps to rotate credentials that were accidentally committed to the repository.

1. Revoke and rotate the exposed key immediately in the system that issued it (Vault or cloud provider).
2. Update secrets in Vault (create new secret at the appropriate path). Example:

   vault kv put secret/ci/org_gh_token value="<NEW_VALUE>"

3. Replace usage in workflows to pull the token from Vault OIDC instead of any PAT.
4. Remove the secret from the working tree and commit the deletion (done in `ops/security/remove-pem-workingtree`).
5. If historical removal is required (recommended for high-risk exposures), coordinate a git history rewrite using `git-filter-repo` or BFG. This must be planned:
   - Identify commits containing the secret (e.g., `git log --all --pretty=format:%H -- <file>`).
   - Run `git-filter-repo --path <path-to-secret> --invert-paths` on a local clone to scrub the file.
   - Force-push branches after team-wide communication and freeze.
6. Rotate any tokens, keys, or certificates that might have been derived from the secret.
7. Verify no automation or external systems still accept the old key.

Contact the security team after rotation and provide the new secret storage location (Vault path) and affected systems.
