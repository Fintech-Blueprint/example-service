# Mesh Validation Evidence

This directory contains validation evidence for service mesh implementation:
- mTLS validation logs
- RBAC validation logs
- Evidence chain hashes

## File Naming Convention

Logs follow the format:
- mTLS logs: `mtls-YYYYMMDD-HHMM.log`
- RBAC logs: `rbac-YYYYMMDD-HHMM.log`

## Evidence Chain Integration

Each log file is:
1. Generated during validation
2. Hashed (SHA256)
3. Referenced in EVIDENCE_CHAIN.md
4. Never modified after creation

## Example Log Structure

```
=== Validation Run ===
Date: YYYY-MM-DD HH:MM:SS UTC
Script: tests/mesh/check-{type}.sh
Branch: phase4/sprint2-mesh
Commit: <git-sha>

=== Configuration ===
Kubernetes Version: <version>
Istio Version: <version>
Cluster: <name>

=== Test Results ===
[detailed test output]

=== Summary ===
Status: [SUCCESS|FAILURE]
Details: [summary text]

=== Evidence ===
Log Hash: SHA256([file content])
```

## Retention Policy

All evidence files are retained indefinitely for audit purposes.