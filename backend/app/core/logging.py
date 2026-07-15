import logging
import logging.config
from pathlib import Path
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file path with timestamp
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOG_FILE),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["file"]
        },
        "alembic": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Apply logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

# Get logger for the app
logger = logging.getLogger("app")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with app prefix"""
    return logging.getLogger(f"app.{name}")
