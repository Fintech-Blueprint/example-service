# 🚨 P1 Incident Report

## Summary
Smoke test failure detected during automated deployment to staging.

## Timeline
- Deployment Start: ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}
- Failure Time: {{ date }}

## Technical Details
### Feature Information
- SHA: {{ feature_sha }}
- PR: ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/pull/{{ pr_number }}

### Failed Component
- [ ] ArgoCD Sync
- [ ] Health Check
- [ ] Resource Validation
- [ ] Other: ________________

### Environment
- Environment: Staging
- Service: example-service
- Deployment SHA: ${GITHUB_SHA}

## Impact
- Severity: P1 (Blocking Deployment)
- Affected Components: Staging Environment
- User Impact: None (caught in pre-production)

## Immediate Actions Taken
- [x] Automatic rollback triggered
- [x] Incident PR created
- [x] Deployment logs captured
- [x] ArgoCD state preserved

## Investigation Checklist
- [ ] Review ArgoCD logs
- [ ] Check resource allocation
- [ ] Validate health check endpoint
- [ ] Review spec coverage report
- [ ] Check resource estimates

## Root Cause Analysis
TBD

## Prevention
### What Went Well
TBD

### What Could Be Improved
TBD

### Action Items
- [ ] Analyze logs
- [ ] Update smoke test criteria if needed
- [ ] Review resource estimates
- [ ] Update documentation

## Resolution
TBD

## Sign-Off
- [ ] Root cause identified
- [ ] Prevention measures documented
- [ ] Runbook updated
- [ ] Stakeholders notified