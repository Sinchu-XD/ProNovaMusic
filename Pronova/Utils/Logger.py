import logging
import sys
import os
from logging.handlers import RotatingFileHandler

LOG_FILE = "logs/pronova.log"

os.makedirs("logs", exist_ok=True)

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] - %(name)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(LOG_FILE, maxBytes=50_000_000, backupCount=10)
    ]
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)
logging.getLogger("ntgcalls").setLevel(logging.WARNING)

LOGGER = logging.getLogger("Pronova")


def set_debug(enabled: bool):
    if enabled:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)
