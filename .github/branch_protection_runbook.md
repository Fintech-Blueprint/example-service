# Branch Protection Runbook

## Minimal Protection Settings

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

## Repositories to Protect
1. example-service
2. platform-libs
3. api-gateway
4. concierge
5. db-manager
6. catalog
7. design-system
8. infra
9. staging-env
10. contracts

## Application Steps
1. Export the organization name:
```bash
export ORG="Fintech-Blueprint"
```

2. Apply protection to each repository's main branch:
```bash
for repo in example-service platform-libs api-gateway concierge db-manager catalog design-system infra staging-env contracts; do
  echo "Protecting $repo..."
  gh api -X PUT "/repos/$ORG/$repo/branches/main/protection" -f required_status_checks='{"strict":true,"contexts":[]}' -f enforce_admins=true -f required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' -f restrictions=null -f allow_force_pushes=false -f allow_deletions=false || echo "Failed to protect $repo"
done
```

3. Verify protection status:
```bash
for repo in example-service platform-libs api-gateway concierge db-manager catalog design-system infra staging-env contracts; do
  echo "Checking $repo..."
  gh api "/repos/$ORG/$repo/branches/main/protection" || echo "Failed to get protection status for $repo"
done
```