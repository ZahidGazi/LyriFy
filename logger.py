import logging
import os

def get_log_file_path():
    # Use APPDATA (or LOCALAPPDATA) to get a user-writable location
    appdata = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
    if not appdata:
        # Fallback: use current directory (not ideal, but works)
        appdata = os.path.abspath(".")
    log_dir = os.path.join(appdata, "LyriFy")
    os.makedirs(log_dir, exist_ok=True)  # Create the directory if it doesn't exist
    return os.path.join(log_dir, "LyriFy.log")

def setup_logger():
    logger = logging.getLogger("LyriFy")
    logger.setLevel(logging.DEBUG)
    
    log_file = get_log_file_path()
    # Create a file handler that logs debug and higher level messages
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    logger.debug(f"Logger initialized, log file at: {log_file}")
    return logger

logger = setup_logger()
