import os
import sys
import re
from loguru import logger
from datetime import date
from dotenv import load_dotenv
import logging

load_dotenv()

log_dir = os.getenv("LOG_DIR", "logs")
log_file = os.getenv("LOG_FILE", "app.log")
os.makedirs(log_dir, exist_ok=True)

app_log_path = os.path.join(log_dir, f"{date.today()}-{log_file}")

logger.remove()

logger.add(
    app_log_path,
    level=os.getenv("LOG_LEVEL", "DEBUG"),
    backtrace=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
    rotation=os.getenv("LOG_MAX_MB", "100MB"),
    retention=int(os.getenv("LOG_BACKUP_COUNT", 5)),
    compression="gz",
)

logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    colorize=False
)

class InterceptHandler(logging.Handler):
    """
    Handler que intercepta logs del sistema estándar de Python y los redirige a Loguru
    """
    ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        message = record.getMessage()
        clean_message = self.ANSI_ESCAPE_PATTERN.sub('', message)

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, clean_message)

intercept_handler = InterceptHandler()

root_logger = logging.getLogger()

root_logger.handlers.clear()
root_logger.addHandler(intercept_handler)
root_logger.setLevel(logging.DEBUG)

# Configurar loggers específicos y evitar propagación para prevenir duplicados
loggers_to_configure = [
    "gunicorn",
    "gunicorn.access", 
    "gunicorn.error",
    "werkzeug",
    "flask",
    "flask.app"
]

for logger_name in loggers_to_configure:
    specific_logger = logging.getLogger(logger_name)
    specific_logger.handlers.clear()
    specific_logger.addHandler(intercept_handler)
    specific_logger.propagate = False
    specific_logger.setLevel(logging.DEBUG)

logging.getLogger().propagate = False