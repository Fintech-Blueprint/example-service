This PR contains small CI and test fixes needed to get the GitHub Actions test matrix green.

Summary of changes:

- Fix: Remove duplicate PYTHONPATH env key in `.github/workflows/test.yml` which caused pre-commit yamllint/actionlint failures.
- Fix: Ensure the package is installable in CI by adding `pip install -e .` and adding missing `__init__.py` files under `src/`.
- Fix: Update tests to import from `src.application.main` and align endpoint paths to `/v1/ping`.
- Fix: Add pytest marker entries to `pyproject.toml` for `unit`, `integration`, and `contract` markers.

Why:
- Pre-commit hooks blocked commits due to the duplicate YAML key.
- CI previously ran pytest with tests deselected (exit code 5) due to mismatched pytest invocation and PYTHONPATH/import issues.

Validation:
- Ran full test matrix in GitHub Actions — all jobs passed in run 17930673199.

Notes:
- No behavior changes to the service code; these are infra/test alignment fixes.
- Recommend keeping `pytest tests/ -m "<marks>"` in the workflow so the matrix drives selection by marker.
