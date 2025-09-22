# Copilot Workflow Guardrails

## 1. Workflow vs Action
- Never confuse GitHub **Workflows** (`.github/workflows/*.yml`) with GitHub **Actions** (`action.yml` or `Dockerfile`).
- If a workflow is meant to be reused, it **must** be defined with:
  ```yaml
  on:
    workflow_call:
  ```
  and consumed with:
  ```yaml
  jobs:
    call-xyz:
      uses: ./.github/workflows/xyz.yml
  ```
- Never try to `uses:` a workflow that does not declare `workflow_call`.

## 2. Lint + Reports
- Every linter step must write output files before artifacts are uploaded.
- Example:
  ```yaml
  - name: Run pylint
    run: pylint src/ > pylint.txt || true
  - name: Upload pylint report
    uses: actions/upload-artifact@v4
    with:
      name: pylint-report
      path: pylint.txt
  ```
- Do this for pylint, black, isort, yamllint, hadolint.
- If reports are not needed → do not create an upload-artifact step. No empty uploads allowed.

## 3. Artifacts
- Never configure upload-artifact without ensuring the file exists.
- Rule of thumb: Generate file first → then upload.
- If optional → guard with `if: always() && hashFiles(...) != ''`.

## 4. Consistent Variable Naming
- Variables must follow the approved list in workflow-vars.md.
- No shadowing between env:, secrets:, and matrix:.

## 5. Lint Policy
- yamllint line length is set to 120 (not 80).
- Long lines are acceptable up to 120 chars. Never enforce <120.

## 6. Green-Only CI Policy
- A workflow job must only fail if real validation fails (lint error, test failure).
- Do not fail for:
  - Missing artifact files.
  - Misinterpreting workflows as actions.
- All “optional” checks must be guarded so they pass cleanly even if skipped.

## 7. Reusable Workflow Rules
- If a workflow is intended to be reusable (`workflow_call`), add a README.md in .github/workflows/ describing:
  - Inputs
  - Outputs
  - Usage example

---

### ✅ What this achieves
- No more red ❌ due to artifacts not found.
- No more "Can't find action.yml" errors (workflows are always declared `workflow_call` if reused).
- No more 80-char spam → line length bumped to 120.
- Copilot is forced to always write reports before uploading.
- CI is **green-only**, failing only for true errors.
