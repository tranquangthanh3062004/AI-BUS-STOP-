"""
shared/logger.py
Structured Logging System with File Rotation and Unicode-safe Output.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from shared.config import settings

LOG_DIR = os.path.dirname(settings.log_file_path)
os.makedirs(LOG_DIR, exist_ok=True)


class UnicodeSafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fallback to ascii representation on Windows console
            msg = self.format(record).encode('ascii', errors='replace').decode('ascii')
            self.stream.write(msg + self.terminator)
            self.flush()


def setup_logger(name: str = "kiosk_app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = RotatingFileHandler(
            settings.log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = UnicodeSafeStreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()
