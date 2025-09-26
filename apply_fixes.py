#!/usr/bin/env python3
import re
import os
import sys
import base64
import json
import requests

TOKEN_PATH = '/tmp/installation.token'
if not os.path.exists(TOKEN_PATH):
    print('Missing token at', TOKEN_PATH)
    sys.exit(1)
TOKEN = open(TOKEN_PATH).read().strip()
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json'}
OWNER = 'Fintech-Blueprint'
REPO = 'example-service'
BRANCH = 'feature/add-ping-endpoint'

files = [
    ('requirements.txt', '/workspaces/test_private/patch_requirements.txt'),
    ('src/application/main.py', '/workspaces/test_private/patch_src_application_main.py'),
    ('tests/unit/test_ping.py', '/workspaces/test_private/patch_tests_unit_test_ping.py'),
    ('tests/contract/test_contract_ping.py', '/workspaces/test_private/patch_tests_contract_test_contract_ping.py'),
]

for target, path in files:
    if not os.path.exists(path):
        print('Missing', path)
        sys.exit(1)

# Edit requirements
req_path = '/workspaces/test_private/patch_requirements.txt'
with open(req_path, 'r+', encoding='utf-8') as f:
    content = f.read()
    if 'requests' not in content:
        if not content.endswith('\n'):
            content += '\n'
        content += 'requests>=2.31.0\n'
        f.seek(0)
        f.write(content)
        f.truncate()
        print('Appended requests to requirements')

# Patch main.py
main_path = '/workspaces/test_private/patch_src_application_main.py'
s = open(main_path, 'r', encoding='utf-8').read()
# Ensure two blank lines before top-level def/class
s = re.sub(r'(?m)(?<!\n\n)(^def |^class )', r'\n\n\1', s)
# Add space after colon when followed by letter/number (simple heuristic)
s = re.sub(r'(?<=\w):(?=\w)', ': ', s)
# write back
open(main_path, 'w', encoding='utf-8').write(s)
print('Patched main.py')

# Patch unit test
t1 = '/workspaces/test_private/patch_tests_unit_test_ping.py'
s = open(t1, 'r', encoding='utf-8').read()
s = re.sub(r'(?m)(?<!\n\n)(^def )', r'\n\n\1', s)
open(t1, 'w', encoding='utf-8').write(s)
print('Patched tests/unit/test_ping.py')

# Patch contract test
t2 = '/workspaces/test_private/patch_tests_contract_test_contract_ping.py'
s = open(t2, 'r', encoding='utf-8').read()
# remove requests imports
s = '\n'.join([ln for ln in s.splitlines() if not re.match(r"^\s*(import requests|from requests import .*)\s*$", ln)])
# ensure blank lines before defs
s = re.sub(r'(?m)(?<!\n\n)(^def |^class )', r'\n\n\1', s)
open(t2, 'w', encoding='utf-8').write(s)
print('Patched tests/contract/test_contract_ping.py')

# Commit each file via Contents API
API_BASE = f'https://api.github.com/repos/{OWNER}/{REPO}/contents'


def put_file(path, localfile, message, branch):
    url = f'{API_BASE}/{path}'
    r = requests.get(url+f'?ref={branch}', headers=HEADERS)
    sha = None
    if r.status_code == 200:
        sha = r.json().get('sha')
    content = base64.b64encode(open(localfile, 'rb').read()).decode()
    body = {'message': message, 'content': content, 'branch': branch}
    if sha:
        body['sha'] = sha
    resp = requests.put(url, headers=HEADERS, data=json.dumps(body))
    if resp.status_code not in (200, 201):
        print('Failed to put', path, resp.status_code, resp.text)
        sys.exit(1)
    print('Updated', path, '->', resp.json().get('commit', {}).get('sha'))


put_file('requirements.txt', req_path, 'chore: add requests to requirements', BRANCH)
put_file('src/application/main.py', main_path, 'fix: flake8 style fixes', BRANCH)
put_file('tests/unit/test_ping.py', t1, 'fix(tests): flake8 spacing', BRANCH)
put_file('tests/contract/test_contract_ping.py', t2, 'fix(tests): remove unused imports', BRANCH)

print('All files updated on branch', BRANCH)
