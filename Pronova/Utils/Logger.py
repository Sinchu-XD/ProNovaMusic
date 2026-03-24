import logging
import sys
import os
from logging.handlers import RotatingFileHandler

LOG_FILE = "logs/pronova.log"

os.makedirs("logs", exist_ok=True)

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] - %(name)s - %(message)s"

logging.basicConfig(
    level=logging.ERROR, 
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(LOG_FILE, maxBytes=50_000_000, backupCount=10)
    ]
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.ERROR)

LOGGER = logging.getLogger("Pronova")
LOGGER.setLevel(logging.ERROR)


def set_debug(enabled: bool):
    if enabled:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.ERROR) 
