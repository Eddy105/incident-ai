.PHONY: install-dev lint test check build

install-dev:
	python -m pip install -e '.[dev]'

lint:
	ruff check .

test:
	pytest

check: lint test

build:
	python -m build
