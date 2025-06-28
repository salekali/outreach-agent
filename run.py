# run.py

from src.utils import load_env, setup_logging
from src.orchestrator import run_outreach_cycle

if __name__ == "__main__":
    load_env()
    logger = setup_logging("orchestrator")

    try:
        logger.info("🚀 Starting Outreach Cycle")
        run_outreach_cycle(logger)
        logger.info("✅ Outreach Cycle Complete")
    except Exception as e:
        logger.error(f"❌ Outreach Cycle Failed: {e}")
