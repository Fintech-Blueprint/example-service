.PHONY: lint test generate

lint:
@echo "Running linters..."
python3 -m flake8 src/ tests/
python3 -m black --check src/ tests/

test:
@echo "Running tests..."
python3 -m pytest tests/ -v

generate:
@echo "Running generator..."
./generator --feature current --idempotent --out=generated

auto-fix-minor:
@echo "Auto-fixing minor issues..."
python3 -m black src/ tests/
python3 -m isort src/ tests/

.PHONY: auto-fix-minor
