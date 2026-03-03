# src/logger.py

import logging
import sys
import os
from datetime import datetime

def setup_logger():
    # Ensure log directory exists and force reconfigure root logger even if configured elsewhere
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/full_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True,
    )

# Per-article debug log dir: reconcile/logs/articleID (path relative to reconcile package)
_RECONCILE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLE_DEBUG_LOGS_DIR = os.path.join(_RECONCILE_ROOT, "logs", "articleID")


def setup_article_debug_logger(article_id: str):
    """
    Create a dedicated file logger for a single article's debug run.
    Log file: reconcile/logs/articleID/{article_id}.log (overwritten each run).
    Returns the logger, or None if article_id is falsy.
    """
    if not article_id or not article_id.strip():
        return None
    os.makedirs(ARTICLE_DEBUG_LOGS_DIR, exist_ok=True)
    log_path = os.path.join(ARTICLE_DEBUG_LOGS_DIR, f"{article_id.strip()}.log")
    name = f"reconcile.article_debug.{article_id}"
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    # Replace handlers so we overwrite the file each run
    logger.handlers.clear()
    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


def get_article_debug_log_path(article_id: str) -> str:
    """Return the absolute path to the per-article debug log file."""
    if not article_id or not article_id.strip():
        return ""
    return os.path.abspath(os.path.join(ARTICLE_DEBUG_LOGS_DIR, f"{article_id.strip()}.log"))


def setup_city_logger(country, city, logs_dir="logs/logs_geonames"):
    os.makedirs(logs_dir, exist_ok=True)
    name = f"{country}_{city}".replace(" ", "_").lower()
    log_path = os.path.join(logs_dir, f"{name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # don’t duplicate to root

    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode="w")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger