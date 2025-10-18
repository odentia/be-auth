.PHONY: venv install run dev lint fmt revision upgrade downgrade

venv:
	python -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -e .

run:
	. .venv/bin/activate && python -m src.api

dev:
	. .venv/bin/activate && UVICORN_RELOAD=1 python -m src.api

lint:
	. .venv/bin/activate && ruff check .

fmt:
	. .venv/bin/activate && ruff format .

revision:
	. .venv/bin/activate && alembic revision -m "initial" --autogenerate

upgrade:
	. .venv/bin/activate && alembic upgrade head

downgrade:
	. .venv/bin/activate && alembic downgrade -1
