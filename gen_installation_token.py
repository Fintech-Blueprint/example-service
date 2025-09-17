#!/usr/bin/env python3
import os,sys,subprocess
# Generate a GitHub App installation token using the private key file
KEY_PATH = '/workspaces/test_private/org-fintech-blueprint-token-admin.2025-09-14.private-key.pem'
APP_ID = 1952259
TOKEN_FILE = '/tmp/installation.token'

# ensure dependencies
try:
    import jwt, requests
except Exception:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyjwt[crypto]', 'requests'])
    import jwt, requests

from time import time

if not os.path.exists(KEY_PATH):
    print('Private key not found at', KEY_PATH)
    sys.exit(1)

with open(KEY_PATH, 'rb') as f:
    private_key = f.read()

now = int(time())
payload = {'iat': now - 60, 'exp': now + (10 * 60), 'iss': str(APP_ID)}
encoded = jwt.encode(payload, private_key, algorithm='RS256')
headers = {'Authorization': f'Bearer {encoded}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/app/installations', headers=headers)
if r.status_code != 200:
    print('Failed to list app installations:', r.status_code, r.text)
    sys.exit(1)
installs = r.json()
if not installs:
    print('No installations found for the app')
    sys.exit(1)
inst_id = None
for it in installs:
    acct = it.get('account', {})
    if acct.get('login') == 'Fintech-Blueprint':
        inst_id = it['id']; break
if not inst_id:
    inst_id = installs[0]['id']

# create installation token
token_url = f'https://api.github.com/app/installations/{inst_id}/access_tokens'
resp = requests.post(token_url, headers=headers)
if resp.status_code not in (200,201):
    print('Failed to create installation token:', resp.status_code, resp.text)
    sys.exit(1)
inst_token = resp.json().get('token')
if not inst_token:
    print('No token in response:', resp.text)
    sys.exit(1)
with open(TOKEN_FILE, 'w') as f:
    f.write(inst_token)
print('Wrote installation token to', TOKEN_FILE)
print('Token preview:', inst_token[:8] + '...')
