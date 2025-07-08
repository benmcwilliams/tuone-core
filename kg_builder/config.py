import yaml
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "extraction_config.yaml"
with open(CONFIG_FILE) as f:
    EXTRACTION_CONFIG = yaml.safe_load(f)