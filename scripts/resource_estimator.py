#!/usr/bin/env python3
"""Resource estimation stub: parses basic hints from feature files and
produces a JSON estimate for CPU, memory, and storage.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / 'reports'
REPORTS.mkdir(parents=True, exist_ok=True)


def estimate():
    # Simple heuristic: base resources + per-feature increments
    features = list((ROOT / 'features').rglob('*.feature'))
    cpu_m = 50  # base 50m
    mem = 64  # base 64Mi
    storage = 5  # base 5Mi

    for f in features:
        text = f.read_text()
        if 'concurrent' in text:
            cpu_m += 50
        if 'database' in text or 'DB' in text:
            mem += 128
            storage += 50

    report = {
        'cpu_m': cpu_m,
        'memory_mib': mem,
        'storage_mib': storage,
        'features_count': len(features)
    }

    with open(REPORTS / 'resource-estimates.json', 'w') as fh:
        json.dump(report, fh, indent=2)

    print('Resource estimate written to', REPORTS / 'resource-estimates.json')


if __name__ == '__main__':
    estimate()
