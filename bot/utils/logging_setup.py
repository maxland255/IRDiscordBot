import sys
import pathlib
import logging
import logging.config

from bot.core.config import get_settings


def setup_logging():
    """Configure logging for the bot"""

    pathlib.Path("logs").mkdir(exist_ok=True)

    # Configuration for the logging system
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,

        # Formatters: define the format of the logs
        'formatters': {
            'console_fmt': {
                '()': 'colorlog.ColoredFormatter',
                'format': '%(log_color)s%(levelname)-8s%(reset)s | %(name)-12s | %(message)s',
                'log_colors': {
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                },
            },
            'file_fmt': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)-15s | %(filename)s:%(lineno)d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },

        # Handlers: define where the logs are sent
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console_fmt',
                'level': get_settings().LOG_LEVEL,
                'stream': sys.stdout,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'file_fmt',
                'filename': 'logs/bot.log',  # The logs are saved in the logs/ folder
                'maxBytes': 1024 * 1024,  # The logs are split in 5 MB chunks
                'backupCount': 5,  # Save the last 5 logs files
                'level': 'DEBUG',  # We write all logs to the file, even INFO and WARNING
                'encoding': 'utf-8',
            },
        },

        # Loggers: define the source of logs
        'loggers': {
            # The principal logger of the bot
            'ir_bot': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,  # Don't propagate to the root logger
            },
            # The logger of the Discord library
            'discord': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',  # We don't want to see all the logs from the Discord library
                'propagate': False,
            },
        },

        # The root logger: define the source of logs for everything else
        'root': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    }

    # Apply the configuration
    logging.config.dictConfig(LOGGING_CONFIG)
