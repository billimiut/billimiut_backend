import os
import logging
import datetime

from logging.handlers import BaseRotatingHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DateRotatingFileHandler(BaseRotatingHandler):
    def __init__(self, dir_path, backupCount=7):
        self.dir_path = dir_path
        self.backupCount = backupCount
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(dir_path, f"{self.current_date}.log")
        super().__init__(filename, mode='a', encoding='utf-8', delay=False)
        self.doRollover()

    def doRollover(self):
        self.stream.close()
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.baseFilename = os.path.join(self.dir_path, f"{self.current_date}.log")
        self.stream = self._open()
        self.cleanup()

    def shouldRollover(self, record):
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return self.current_date != current_date

    def emit(self, record):
        if self.shouldRollover(record):
            self.doRollover()
        super().emit(record)

    def cleanup(self):
        log_files = sorted(
            [f for f in os.listdir(self.dir_path) if f.endswith(".log")],
            reverse=True
        )
        for log_file in log_files[self.backupCount:]:
            os.remove(os.path.join(self.dir_path, log_file))


log_file_handler = DateRotatingFileHandler("./logs/", backupCount=7)

formatter = logging.Formatter('%(levelname)s %(message)s')
log_file_handler.setFormatter(formatter)

logger.addHandler(log_file_handler)


def info(message):
    logger.info(message)


def debug(message):
    logger.debug(message)


def error(message):
    logger.error(message)


def warning(message):
    logger.warning(message)


def critical(message):
    logger.critical(message)