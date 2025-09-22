```markdown
# Contributing to example-service

Please open PRs against `main`. Ensure tests, linting, and a contract test (if applicable) pass. Follow code review guidelines.
```

## No Local Drift (pre-push hook)

To reduce accidental drift between local developer environments and CI enforcement, we provide a Git hook that prevents pushing when there are uncommitted changes. To enable it locally run:

	git config core.hooksPath .githooks

This repository includes a `.githooks/pre-push` script which will block pushes if your working tree has uncommitted changes. The intention is to make sure artifacts produced by generators and enforcement scripts are committed before pushing.

If you prefer not to enable the hook globally, you may opt to run the validations locally as part of your pre-push checks. CI will still enforce checks during PR evaluation.

If you need help enabling hooks or have a legitimate workflow that requires bypassing the hook (e.g., CI automation), contact the repo administrators.
# Contributing to example-service\n\nPlease open PRs against `main`. Ensure tests, linting, and a contract test (if applicable) pass. Follow code review guidelines.
