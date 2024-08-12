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
# 기존의 BaseRotatingHandler를 커스텀 한 것
# 본래 BaseRotatingHandler는 일정 주기로 새로 로그 생성 + 로그 파일 개수 관리만 해주는데, 이것을 날짜 기준으로 구분하기 쉽도록 매일 자정 해당 날짜 이름의 로그파일을 생성하고 최신 7개를 유지하도록 커스텀
# 내부 메서드명이 BaseRotatingHandler 메서드를 override 한 것 같아서 카멜케이스지만 굳이 스네이크 케이스로 변경하지 않음


log_file_handler = DateRotatingFileHandler("./logs/", backupCount=7)
# 로그 파일 관리할 핸들러로 위에서 커스텀한 핸들러를 사용한다. 로그 저장위치는 현재 디렉토리의 logs 폴더이고, 로그 개수는 7개를 유지한다. (backupCount)

formatter = logging.Formatter('%(levelname)s %(message)s')
log_file_handler.setFormatter(formatter)
# 로그 포맷 정보를 커스텀 핸들러에 추가해준다.

logger.addHandler(log_file_handler)
# 핸들러를 로거에 추가한다.


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