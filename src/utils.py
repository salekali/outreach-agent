# src/utils.py

import os
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load .env or secrets file automatically
def load_env():
    secrets_path = Path("secrets.env.sops")
    dotenv_path = Path(".env")

    if secrets_path.exists():
        load_dotenv(secrets_path)
    elif dotenv_path.exists():
        load_dotenv(dotenv_path)
    else:
        print("⚠️ No .env or secrets.env.sops file found.")

# Safe int cast with fallback
def safe_int(val, fallback=0):
    try:
        return int(val)
    except:
        return fallback

# Setup logging
def setup_logging(name="agent", level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
