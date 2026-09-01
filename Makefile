.PHONY: install run up down test lint format

install:
	python -m pip install -e '.[dev]'

run:
	uvicorn app.main:app --reload

up:
	docker compose up --build -d

down:
	docker compose down

test:
	pytest -q

lint:
	ruff check .
	mypy app

format:
	ruff format .
	ruff check --fix .
