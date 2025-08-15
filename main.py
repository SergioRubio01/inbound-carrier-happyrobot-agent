import logging
import multiprocessing
import os
import sys

import uvicorn

# Assume logger is configured elsewhere or configure basic here
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Process handling --- #

def _run_api_server():
    """Runs the main HappyRobot FastAPI server."""
    try:
        host = os.environ.get("HOST", "127.0.0.1")  # Default to localhost for safety
        port = int(os.environ.get("PORT", "8000"))
        reload = os.environ.get("ENVIRONMENT", "prod").lower() == "dev"
        log_level = os.environ.get("LOG_LEVEL", "info").lower()

        logger.info(f"Starting HappyRobot API Server on {host}:{port}...")
        uvicorn.run(
            "src.interfaces.api.app:create_app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            factory=True,
        )
    except Exception:
        logger.exception("HappyRobot API Server failed to start.")
        sys.exit(1)


    # The API server running via uvicorn handles its own signal shutdown gracefully
    logger.info("Exiting main process.")
    sys.exit(0)


def main():
    """Main entry point"""

    # Run API server in the main process
    # Uvicorn will take over the main thread here
    logger.info("Starting API server...")
    _run_api_server()


if __name__ == "__main__":
    # Required for multiprocessing correctly on Windows
    multiprocessing.freeze_support()
    main()
