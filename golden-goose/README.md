# Golden Goose Release Management

## Overview
Golden Goose is the release packaging and management system for compliant service releases.

## Directory Structure
```
golden-goose/
├── config.yaml           # Configuration and policies
├── releases/            # Release packages
│   └── v1.0.0/         # Example release
│       ├── manifest.json    # Release manifest
│       ├── sbom/           # SBOM reports
│       ├── compliance/     # Compliance evidence
│       ├── dashboards/     # Grafana dashboards
│       └── signatures/     # Release signatures
└── scripts/             # Management scripts
    ├── package.sh      # Create release package
    ├── verify.sh       # Verify package integrity
    └── rollback.sh     # Handle rollbacks
```

## Release Process
1. Compliance validation
2. Artifact collection
3. Package creation
4. Signature generation
5. Manifest creation
6. Package verification

## Features
- Snapshot management
- DR backup support
- Dashboard versioning
- Evidence referencing
- Secret reference management

## Usage
```bash
# Create new release
./scripts/package.sh v1.0.0

# Verify release
./scripts/verify.sh v1.0.0

# Rollback to release
./scripts/rollback.sh v1.0.0
```

## Policies
- Snapshots are signed and immutable
- DR backups retain full history
- Evidence is referenced, never copied
- Secrets are referenced via Vault paths
- Dashboards are versioned with releases