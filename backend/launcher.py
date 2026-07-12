"""Frozen-app launcher for the desktop backend sidecar.

This wrapper exists so import/startup failures are written to a user-visible
log file instead of disappearing when the Windows subsystem hides the console.
"""

from __future__ import annotations

import logging
import traceback

from backend.runtime_paths import runtime_file


LOG_FILE = runtime_file("logs/backend.log")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
    force=True,
)
logger = logging.getLogger("investment.launcher")


def run() -> None:
    try:
        from backend.main import run_server

        logger.info("Starting backend sidecar; log file: %s", LOG_FILE)
        run_server()
        logger.error("Backend server exited")
    except BaseException:
        logger.critical("Backend sidecar failed to start:\n%s", traceback.format_exc())
        raise


if __name__ == "__main__":
    run()
