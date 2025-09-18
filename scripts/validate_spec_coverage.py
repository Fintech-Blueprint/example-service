#!/usr/bin/env python3
"""
Hardened validator for spec-coverage.json.

Checks each .feature referenced in the generated files (or scans features/) and
verifies each Scenario contains Given, When, Then steps. Produces detailed
errors in the spec-coverage.json file and prints a human-readable log.

Exit codes:
  0 - OK (no violations)
  1 - Violations found
  2 - Missing/unreadable spec-coverage.json or IO errors
"""
import argparse
import json
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


GIVEN_RE = re.compile(r'\bGiven\b', re.IGNORECASE)
WHEN_RE = re.compile(r'\bWhen\b', re.IGNORECASE)
THEN_RE = re.compile(r'\bThen\b', re.IGNORECASE)


def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def load_json(path: Path) -> Any:
    if not path.exists():
        print(f'Report not found: {path}')
        sys.exit(2)
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f'Failed to read/parse JSON {path}: {e}')
        sys.exit(2)


def scan_feature(path: Path) -> List[Dict[str, Any]]:
    """Return a list of violations found in a .feature file by scenario."""
    violations = []
    try:
        text = path.read_text()
    except Exception as e:
        return [{"file": str(path), "line": 0, "issue": f"unreadable: {e}"}]

    lines = text.splitlines()
    current_scenario = None
    scenario_start = None
    buffer = []
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if line.lower().startswith('scenario'):
            # flush previous
            if current_scenario is not None:
                violations.extend(check_scenario_fields(path, current_scenario, scenario_start, buffer))
            current_scenario = line
            scenario_start = i
            buffer = []
            continue
        if current_scenario is not None:
            buffer.append((i, line))

    # flush last
    if current_scenario is not None:
        violations.extend(check_scenario_fields(path, current_scenario, scenario_start, buffer))

    return violations


def check_scenario_fields(path: Path, scenario_line: str, start_line: int, buffer: List) -> List[Dict[str, Any]]:
    has_given = False
    has_when = False
    has_then = False
    for ln, text in buffer:
        if GIVEN_RE.search(text):
            has_given = True
        if WHEN_RE.search(text):
            has_when = True
        if THEN_RE.search(text):
            has_then = True

    issues = []
    if not has_given:
        issues.append({"file": str(path), "line": start_line, "issue": "missing Given"})
    if not has_when:
        issues.append({"file": str(path), "line": start_line, "issue": "missing When"})
    if not has_then:
        issues.append({"file": str(path), "line": start_line, "issue": "missing Then"})
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True, help='Path to spec-coverage.json')
    parser.add_argument('--features-dir', required=False, default='features', help='Directory with .feature files')
    args = parser.parse_args()

    report_path = Path(args.report)
    report = load_json(report_path)

    # Discover feature files referenced in generated files first, else scan features/
    referenced = []
    gen_files = Path('generated').glob('**/generated_files.json')
    for gf in gen_files:
        try:
            g = json.loads(gf.read_text())
            referenced.extend(g.get('generated', []))
        except Exception:
            pass

    feature_paths = []
    for r in referenced:
        p = Path(r)
        if p.suffix == '.feature' and p.exists():
            feature_paths.append(p)

    if not feature_paths:
        feature_paths = list(Path(args.features_dir).glob('**/*.feature'))

    all_violations = []
    for fp in feature_paths:
        v = scan_feature(fp)
        all_violations.extend(v)

    # Update report with detailed errors
    report['errors'] = all_violations
    report['checked_at'] = now_iso()
    report['checked_files'] = [str(p) for p in feature_paths]

    # Write back the report
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2))
    except Exception as e:
        print(f'Failed to write report {report_path}: {e}')
        sys.exit(2)

    # Human-readable output
    print('Spec coverage check:')
    print(f"  features scanned: {len(feature_paths)}")
    print(f"  violations found: {len(all_violations)}")
    if all_violations:
        print('\nViolations:')
        for it in all_violations:
            print(f" - {it.get('file')}:{it.get('line')} - {it.get('issue')}")
        sys.exit(1)

    print('\nSpec coverage OK.')
    sys.exit(0)


if __name__ == '__main__':
    main()
