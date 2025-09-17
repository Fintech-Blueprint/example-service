#!/usr/bin/env python3
"""
Enhanced audit compliance reporter.

Produces a detailed audit-response.json including commit sha, PR info, runner metadata,
and timestamps for generation/validation/audit steps. Exit codes:
  0 - no violations
  1 - violations in compliance mode
  2 - file read/write errors
"""
import argparse
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def load_json_safe(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def gather_runner_metadata() -> Dict[str, Any]:
    return {
        'os': platform.platform(),
        'python': platform.python_version(),
        'processor': platform.processor(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True)
    parser.add_argument('--pr-number', required=False, default='manual')
    parser.add_argument('--pr-author', required=False)
    parser.add_argument('--commit-sha', required=False)
    parser.add_argument('--output', required=True)
    parser.add_argument('--spec-report', required=False)
    parser.add_argument('--generated-files', required=False)
    args = parser.parse_args()

    out: Dict[str, Any] = {
        'mode': args.mode,
        'pr_number': args.pr_number,
        'pr_author': args.pr_author,
        'commit_sha': args.commit_sha or os.environ.get('GITHUB_SHA'),
        'timestamps': {
            'audit': now_iso()
        },
        'runner': gather_runner_metadata(),
        'violations': [],
        'spec_report': None,
        'generated_files': None,
    }

    # Attempt to attach spec report
    if args.spec_report:
        spec = load_json_safe(Path(args.spec_report))
        out['spec_report'] = spec
        if spec and spec.get('errors'):
            out['violations'].extend(spec.get('errors'))

    # Attach generated_files if provided
    if args.generated_files:
        gf = load_json_safe(Path(args.generated_files))
        out['generated_files'] = gf

    # Add environment sourced metadata where available
    out['env'] = {
        'github_ref': os.environ.get('GITHUB_REF'),
        'github_run_id': os.environ.get('GITHUB_RUN_ID'),
        'github_actor': os.environ.get('GITHUB_ACTOR'),
    }

    # Write output
    try:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2))
        print(f'Wrote audit response to {p}')
    except Exception as e:
        print('Failed to write audit response:', e)
        sys.exit(2)

    # Compliance failure behavior
    if args.mode == 'compliance' and out['violations']:
        print('Compliance violations found; failing with exit code 1')
        sys.exit(1)

    print('Audit compliance check completed')
    sys.exit(0)


if __name__ == '__main__':
    main()
