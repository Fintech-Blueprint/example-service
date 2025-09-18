#!/usr/bin/env python3
"""Generate hexagonal code, tests, and docs from .feature BDD files using Jinja2 templates.

Usage: python scripts/generate_from_spec.py
"""
import json
import os
from pathlib import Path
import sys

try:
    from jinja2 import Environment, FileSystemLoader
except Exception:
    print('Missing dependency: jinja2. Install with `pip install jinja2`')
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / 'templates'
REPORTS_DIR = ROOT / 'reports'


def slugify(name: str) -> str:
    return name.strip().lower().replace(' ', '_')


def titleize(name: str) -> str:
    return ''.join(part.capitalize() for part in name.split('_'))


def parse_feature(path: Path):
    text = path.read_text()
    feature = None
    scenarios = []
    lines = text.splitlines()
    cur_scenario = None
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if line.startswith('Feature:'):
            feature = line.split(':', 1)[1].strip()
        elif line.startswith('Scenario:'):
            if cur_scenario:
                scenarios.append(cur_scenario)
            cur_scenario = {'title': line.split(':', 1)[1].strip(), 'line': i, 'steps': []}
        elif cur_scenario and (line.startswith('Given ') or line.startswith('When ') or line.startswith('Then ') or line.startswith('And ')):
            cur_scenario['steps'].append(line)
    if cur_scenario:
        scenarios.append(cur_scenario)
    return feature, scenarios


def validate_scenarios(scenarios):
    issues = []
    implemented = 0
    for s in scenarios:
        has_given = any(st.startswith('Given ') for st in s['steps'])
        has_when = any(st.startswith('When ') for st in s['steps'])
        has_then = any(st.startswith('Then ') for st in s['steps'])
        if not (has_given and has_when and has_then):
            issues.append({'line': s['line'], 'title': s['title'], 'issue': 'Incomplete scenario steps'})
        else:
            implemented += 1
    return implemented, issues


def render_templates(feature_name, scenarios):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), keep_trailing_newline=True)
    slug = slugify(feature_name)
    title = titleize(slug)

    outputs = []

    # core service
    tpl = env.get_template('service.py.j2')
    core_path = ROOT / f'src/core/{slug}'
    core_path.mkdir(parents=True, exist_ok=True)
    service_file = core_path / 'service.py'
    service_file.write_text(tpl.render(class_name=f'{title}Service'))
    outputs.append(str(service_file))

    # adapter controller
    tpl = env.get_template('controller.py.j2')
    adapters_path = ROOT / f'src/adapters/http'
    adapters_path.mkdir(parents=True, exist_ok=True)
    controller_file = adapters_path / f'{slug}_controller.py'
    controller_file.write_text(tpl.render(endpoint='/' + slug, class_name=f'{title}Service'))
    outputs.append(str(controller_file))

    # ensure src/main.py exists and includes router
    main_file = ROOT / 'src/main.py'
    if not main_file.exists():
        main_file.parent.mkdir(parents=True, exist_ok=True)
        main_file.write_text('from fastapi import FastAPI\n\napp = FastAPI()\n')
        outputs.append(str(main_file))
    # append import/include if not present
    main_text = main_file.read_text()
    include_line = f"from src.adapters.http.{slug}_controller import router as {slug}_router"
    include_router = f"app.include_router({slug}_router)"
    if include_line not in main_text:
        main_file.write_text(main_text + '\n' + include_line + '\n' + include_router + '\n')

    # unit test
    tpl = env.get_template('unit_test.py.j2')
    tests_unit_path = ROOT / 'tests/unit'
    tests_unit_path.mkdir(parents=True, exist_ok=True)
    unit_file = tests_unit_path / f'test_{slug}_service.py'
    unit_file.write_text(tpl.render(class_name=f'{title}Service', module=f'src.core.{slug}.service'))
    outputs.append(str(unit_file))

    # integration test
    tpl = env.get_template('integration_test.py.j2')
    tests_integ_path = ROOT / 'tests/integration'
    tests_integ_path.mkdir(parents=True, exist_ok=True)
    integ_file = tests_integ_path / f'test_{slug}_endpoint.py'
    integ_file.write_text(tpl.render(endpoint='/' + slug))
    outputs.append(str(integ_file))

    # docs
    tpl = env.get_template('docs.md.j2')
    docs_path = ROOT / 'docs'
    docs_path.mkdir(parents=True, exist_ok=True)
    docs_file = docs_path / f'{slug}.md'
    docs_file.write_text(tpl.render(feature=feature_name))
    outputs.append(str(docs_file))

    return outputs


def run():
    features = list((ROOT / 'features').rglob('*.feature'))
    if not features:
        print('No feature files found under features/. Create features/*.feature to generate code.')
        return 1

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    all_generated = []
    total = 0
    total_impl = 0
    errors = []

    for f in features:
        feature_name, scenarios = parse_feature(f)
        if not feature_name:
            errors.append({'file': str(f), 'issue': 'Missing Feature title'})
            continue
        implemented, issues = validate_scenarios(scenarios)
        total += len(scenarios)
        total_impl += implemented
        if issues:
            for it in issues:
                e = {'file': str(f), 'line': it['line'], 'issue': it['issue']}
                errors.append(e)
            # Fail generation if there are missing steps
            print(f'Found issues in {f}:', issues)
            continue

        outputs = render_templates(feature_name, scenarios)
        all_generated.extend(outputs)

    spec_coverage = round((total_impl / total * 100) if total > 0 else 0, 2)
    report = {
        'spec_coverage': spec_coverage,
        'total_scenarios': total,
        'implemented_scenarios': total_impl,
        'errors': errors,
        'generated_files': all_generated,
    }
    with open(REPORTS_DIR / 'spec-coverage.json', 'w') as fh:
        json.dump(report, fh, indent=2)

    # run resource estimator
    os.system(f'python {ROOT / "scripts/resource_estimator.py"}')

    with open(REPORTS_DIR / 'generated_files.json', 'w') as fh:
        json.dump(all_generated, fh, indent=2)

    print('Generation complete. Report written to', REPORTS_DIR / 'spec-coverage.json')
    return 0


if __name__ == '__main__':
    sys.exit(run())
