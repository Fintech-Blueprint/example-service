.PHONY: all lint test clean

PYTHON_FILES := $(shell find . -name "*.py")
CPP_FILES := $(shell find . -name "*.cpp" -o -name "*.hpp")
COVERAGE_THRESHOLD := 80

all: lint test

lint: lint-python lint-cpp

lint-python:
	@echo "Running Python linter..."
	flake8 $(PYTHON_FILES)

lint-cpp:
	@echo "Running C++ linter..."
	@if [ -n "$(CPP_FILES)" ]; then \
		clang-tidy $(CPP_FILES) -- -std=c++17; \
	else \
		echo "No C++ files to lint"; \
	fi

test: test-python test-cpp

test-python:
	@echo "Running Python tests with coverage..."
	pytest --cov=src --cov-report=term-missing --cov-fail-under=$(COVERAGE_THRESHOLD) tests/

test-cpp:
	@echo "Running C++ tests..."
	@if [ -d "build" ]; then \
		cd build && ctest --output-on-failure; \
	else \
		echo "No C++ tests to run"; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ __pycache__/ .pytest_cache/ .coverage reports/