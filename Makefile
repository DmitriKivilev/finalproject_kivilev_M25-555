.PHONY: install run project format lint test build publish package-install

install:
	poetry install

run:
	poetry run python main.py

project:
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
