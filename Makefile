.PHONY: run decrypt env install clean

run:
	python3 run.py

encrypt:
	sops -e config/.env > config/.env.enc

decrypt:
	sops -d config/.env.enc > config/.env

env:
	python3 -c 'from src.utils import load_env; load_env()'

install:
	python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
