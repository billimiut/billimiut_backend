import logging.config

# set up logging
logging.config.fileConfig("log.ini")
logger = logging.getLogger('sLogger')


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