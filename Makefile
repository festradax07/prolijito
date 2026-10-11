.PHONY: install format lint typecheck imports test check

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
