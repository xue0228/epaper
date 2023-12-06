import os

from loguru import logger

from constants import LOG_DIR

logger.add(
    os.path.join(LOG_DIR, "{time}.log"),
    rotation="200KB",
    retention="72h",
    level="INFO",
)
