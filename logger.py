import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Path(__file__) grabs the relative path of the curr file
# .resolve(): opens that up to the absolute path
# .parent: only gets the parent path rather than the specific item itself.
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / '.env')

# ----- Adjust this section per project -----
LOG_FOLDER_NAME = 'logs'
LOG_FILE_NAME = 'smart-plug-automation.log'
LOGGER_NAME = 'smart-plug-automation-logger'
# -------------------------------------------

LOG_DIR = BASE_DIR / LOG_FOLDER_NAME # C:\Users\chris\TP_CodingFolder\03_PersonalLab\00_HomeLab\smart-plug-automation + \logs
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME # C:\Users\chris\TP_CodingFolder\03_PersonalLab\00_HomeLab\smart-plug-automation\logs + \smart-plug-automation.log

# Create log folder directory if it doesn't exist already.
# parents=True makes parent folders if necessary (logs)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_STATE = os.getenv('LOG_STATE', 'info')
LOG_ONLY = str(os.getenv('LOG_ONLY', 'False')).lower() in ('true', '1', 't') # Handles multiple version of True. Is still a boolean

MAX_BYTES = 5 * 1024 * 1024 # 5MB
BACKUP_COUNT = 3

rotate_handler = RotatingFileHandler(
    LOG_FILE_PATH,
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
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)