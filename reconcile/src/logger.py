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