# Audit Evidence Directory

## Overview
This directory contains compliance and audit evidence with the following characteristics:

- Retention: 3 years minimum
- Format: JSON, signed with hash chain
- Immutable: never delete, only append

## Contents
- SAST results
- Test evidence
- Compliance approvals
- Secret rotation logs
- Load test results
- Security scan reports

## Structure
```
audit/
  YYYY/
    MM/
      DD/
        - sast/          # Static Analysis Security Testing results
        - tests/         # Test execution evidence
        - compliance/    # Compliance validation results
        - secrets/       # Secret rotation audit logs
        - load-tests/    # Performance test results
        - security/      # Security scan reports
```

## Immutability
All evidence is stored with:
- Timestamps
- Hash chains
- Digital signatures
- Append-only logs

## Retention Policy
- Minimum retention: 3 years
- Format: Immutable JSON reports
- Storage: Hash-chained for tampering protection
- Access: Read-only after creation

## Integration
- CI/CD pipelines automatically store evidence
- Golden Goose releases reference evidence
- Rollbacks maintain evidence integrity