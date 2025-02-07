import logging
import os

LOG_FILE = "LyriFy.log"

def setup_logger():
    logger = logging.getLogger("LyriFy")
    logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger  = setup_logger()
