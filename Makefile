.PHONY: install run test lint format

install:
	pip install -e ".[dev]"

run:
	uvicorn trade_service_agents.api.app:app --reload

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests
