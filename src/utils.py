from pathlib import Path
import logging
import yaml
from dotenv import load_dotenv

# Load settings from YAML file
def load_settings(path="config/settings.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# Load .env or secrets file automatically
def load_env():
    secrets_path = Path("config/.env")
    if secrets_path.exists():
        load_dotenv(secrets_path)
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
