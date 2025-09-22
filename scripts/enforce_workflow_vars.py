#!/usr/bin/env python3
import sys
import re
from pathlib import Path

ALLOWED_VARS = {
    'VAULT_ADDR', 'VAULT_ROLE', 'ORG_GH_TOKEN', 'CI_ENV', 'PYTHON_VERSION', 'TEST_TYPE',
    'python-version', 'test-type', 'lint-type', 'check-type', 'vault-role', 'test-path', 'test-marks',
    'ACTIONS_ID_TOKEN_REQUEST_TOKEN'
}

VAR_PATTERN = re.compile(r'\${{ *(secrets|env|matrix)\.([A-Za-z0-9_\-]+) *}}')

errors = []

for yml in Path('.github/workflows').glob('*.yml'):
    with yml.open() as f:
        for i, line in enumerate(f, 1):
            for match in VAR_PATTERN.finditer(line):
                var = match.group(2)
                if var not in ALLOWED_VARS:
                    errors.append(f"{yml}:{i}: Invalid variable: {match.group(0)}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
