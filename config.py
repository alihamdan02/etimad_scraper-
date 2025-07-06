import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "ali"),
    "password": os.getenv("MYSQL_PASSWORD", "yourpassword"),
    "database": os.getenv("MYSQL_DATABASE", "etimad_tenders"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "pool_size": 5,
    "pool_name": "etimad_pool",
    "autocommit": True
}

# Logging configuration
LOGGING_CONFIG = {
     "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "unicode": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            "encoding": "utf-8"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "unicode",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "etimad_scraper.log",
            "formatter": "unicode",
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "etimad": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

# Scraper configuration
SCRAPER_CONFIG = {
    "max_retries": 3,
    "timeout": 60000,
    "concurrent_requests": 5,
    "batch_size": 20
}

MAIN_TO_SUB = {
    "ادارة البيانات": ["حوكمة البيانات", "استراتيجية البيانات", "ذكاء الأعمال"],
}

