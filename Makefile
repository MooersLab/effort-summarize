# Makefile for time-tracking summary scripts
# ──────────────────────────────────────────────

PYTHON   ?= python3
PYTEST   ?= $(PYTHON) -m pytest
COVERAGE ?= $(PYTHON) -m coverage

SRC      = weeklySummary.py monthSummary.py
TESTS    = test_weeklySummary.py test_monthSummary.py conftest.py

.PHONY: help test coverage coverage-html lint clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

test:  ## Run the full test suite with verbose output
	$(PYTEST) -v $(TESTS)

coverage:  ## Run tests and print a coverage report to the terminal
	$(COVERAGE) run --source=. --omit='test_*,conftest*' -m pytest -v $(TESTS)
	$(COVERAGE) report -m --omit='test_*,conftest*'

coverage-html:  ## Generate an HTML coverage report in htmlcov/
	$(COVERAGE) run --source=. --omit='test_*,conftest*' -m pytest -v $(TESTS)
	$(COVERAGE) html --omit='test_*,conftest*'
	@echo "Open htmlcov/index.html in your browser."

lint:  ## Run flake8 linter on source and test files
	$(PYTHON) -m flake8 $(SRC) $(TESTS) --max-line-length=100

clean:  ## Remove generated files
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -name '*.pyc' -delete
