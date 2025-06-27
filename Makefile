.PHONY: run decrypt env install clean

run:
	python run.py

decrypt:
	sops -d secrets.env.sops > .env

env:
	python -c 'from src.utils import load_env; load_env()'

install:
	python -m venv venv && . venv/bin/activate && pip install -r requirements.txt

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
