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
