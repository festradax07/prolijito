.PHONY: install format lint typecheck imports test test-system check image fixtures-pdf

install:
	pip install -e '.[dev]'
	pre-commit install

format:
	ruff format .
	ruff check --fix .

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy

imports:
	lint-imports

test:
	pytest -m "not system"

check: lint typecheck imports test

test-system:
	pytest -m system --no-cov

image:
	docker build -t prolijito:dev .

fixtures-pdf:
	tests/fixtures/pdf/build.sh
