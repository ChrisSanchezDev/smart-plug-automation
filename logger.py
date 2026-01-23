import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

# ----- Adjust this section per project -----
RELATIVE_LOG_FILE = 'scripts/smart-plug-automation/logs/smart-plug-automation.log'
LOGGER_NAME = 'smart-plug-automation-logger'
# -------------------------------------------

home_dir = os.path.expanduser('~')
LOG_FILE = os.path.join(home_dir, RELATIVE_LOG_FILE)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

LOG_STATE = os.getenv('LOG_STATE')
LOG_ONLY = bool(os.getenv('LOG_ONLY'))

MAX_BYTES = 5 * 1024 * 1024 # 5MB
BACKUP_COUNT = 3

rotate_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=MAX_BYTES,
    backupCount=BACKUP_COUNT
)

# Standard format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
rotate_handler.setFormatter(formatter)

# Setting up logger object for importing
logger = logging.getLogger(LOGGER_NAME)
if LOG_STATE == 'debug':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
logger.addHandler(rotate_handler)

if not LOG_ONLY:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)