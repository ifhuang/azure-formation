from os.path import (
    realpath,
    dirname
)
import logging
import logging.config


class Log(object):

    def __init__(self):
        logging.config.fileConfig("%s/logging.conf" % dirname(realpath(__file__)))
        self.logger = logging.getLogger("myLogger")

    def debug(self, debug):
        self.logger.debug(debug)

    def info(self, info):
        self.logger.info(info)

    def warn(self, warn):
        self.logger.warn(warn)

    def error(self, error):
        self.logger.error(str(error))

    def critical(self, critical):
        self.logger.critical(critical)

# usage(make sure /var/log/azure-formation/ directory exists and accessible):
# from log import log
# log.info("some info")
log = Log()