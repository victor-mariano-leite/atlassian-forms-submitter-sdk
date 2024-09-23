install:
	@pip install -r requirements/all.txt
	@pip install pre-commit
	@pre-commit install
	@mypy --install-types
	
prepare:
	@black . -v
	@isort .
	@mypy atlassianforms
	@pylint atlassianforms
	@flake8 atlassianforms
	@echo Good to Go!

check:
	@black . -v --check
	@isort . --check
	@mypy atlassianforms
	@flake8 atlassianforms
	@pylint atlassianforms
	@echo Good to Go!

docs:
	@mkdocs build --clean

docs-serve:
	@mkdocs serve

test:
	@pytest --cov atlassianforms

test-cov:
	@pytest --cov atlassianforms --cov-report xml:coverage.xml
.PHONY: docs
