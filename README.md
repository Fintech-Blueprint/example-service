# Example Service (Golden Template)

This is the golden template service for the Fintech-Blueprint organization.
Every new microservice should be cloned from this repository.

## Architecture
- Hexagonal structure:
  - src/domain → business rules (pure logic, no dependencies)
  - src/application → use cases, API entrypoints (FastAPI here)
  - src/infrastructure → DB, queues, external systems
  - src/adapters → bridges between infra and domain

## Running Locally
```bash
pip install -r requirements.txt
uvicorn src.application.main:app --reload
```

Check: http://localhost:8000/healthz

## Running Tests
```
pytest
```

## Docker
```
docker build -t example-service .
docker run -p 8000:8000 example-service
```

## CI/CD

Pull Requests: lint + tests + SAST + SBOM + sign

Main branch: builds a Docker image

Future: staging deployment (Kubernetes)

## How to Create a New Service

Duplicate this repo.

Replace example-service with your service name.

Implement your domain logic under src/domain/.

Expose new APIs under src/application/.

Submit PR → CI/CD enforces gates.

## AI Onboarding & Org Token Guide

This repository includes automation and AI-driven generation workflows. To let a new AI session (or another automation agent) continue work, follow these steps.

1. Create an organization access token (short-lived recommended):

  - Go to GitHub Settings → Developer settings → Personal access tokens.
  - Create a token with `repo` and `workflow` scopes (and `admin:org` if you need org-level discovery).
  - Store the token securely. In this workspace we use an ephemeral file path for CI: `/tmp/installation.token`.

2. Provide the token to the environment where the AI runs:

  - Locally: `export GITHUB_TOKEN=ghp_...` or write to `/tmp/installation.token` and ensure file permissions are secure.
  - In CI: add the token as a repository secret and reference it via the workflow.

3. Quick start for a new AI session to explore the org and repo:

  - Ensure the token is available at `/tmp/installation.token` or as `GITHUB_TOKEN` env var.
  - From the workspace root run the common checks:

```bash
python3 - <<'PY'
import requests,os
TOKEN=open('/tmp/installation.token').read().strip() if os.path.exists('/tmp/installation.token') else os.environ.get('GITHUB_TOKEN')
headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json'}
owner='Fintech-Blueprint'; repo='example-service'
print(requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers).json())
PY
```

4. How the AI should continue work (recommended sequence):

  - Validate open PRs and required checks.
  - Run `validate-specs.yml` and `auto-generate.yml` for new specs.
  - When generating code, always run `flake8` and `pytest` locally before creating PRs.

5. Security & governance notes:

  - Do not store long-lived tokens in the repo. Use short-lived tokens or GitHub App installations.
  - The AI must honor `.copilot-instructions.md` for workflow generation rules and the Spec-to-System policies.

6. Contact & audit

  - Generated runs deposit reports under `reports/` and `audit-reports/` in the repository and as GitHub Actions artifacts.
  - If a run fails Compliance checks, the AI must create an issue and tag the spec owner; do not attempt silent fixes.

With these steps, a new AI session can pick up the repository, discover specs, run generation, and open PRs while following governance and traceability rules.
