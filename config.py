import os
import json
from logger import logger

# Define config path inside user's AppData folder
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "LyriFy")
os.makedirs(APPDATA_DIR, exist_ok=True)  # Ensure directory exists

CONFIG_FILE = os.path.join(APPDATA_DIR, "config.json")

def save_config(config):
    """Save configuration to AppData"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def load_config():
    """Load configuration from AppData"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    return {}
