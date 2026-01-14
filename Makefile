.PHONY: install run format lint test

install:
	poetry install

run:
	poetry run python main.py

format:
	poetry run ruff format .

lint:
	poetry run ruff check .

build:
	poetry build

publish:
	poetry publish

package-install:
	pip install dist/*.whl
