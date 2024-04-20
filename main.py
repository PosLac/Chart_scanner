import sys

from PyQt5.QtWidgets import QApplication

import view
from config import config

logger = config.logger

if __name__ == "__main__":
    # logger.debug('This is a debug message, displayed in gray (dim white).')
    # logger.info('This is an info message, also displayed in gray (dim white).')
    # logger.warning('This is a warning message, displayed in yellow.')
    # logger.error('This is an error message, displayed in red.')
    # logger.critical('This is a critical message, displayed in red with white background.')

    # faulthandler.enable()
    # logger.info("Main started")
    app = QApplication(sys.argv)
    inputWindow = view.InputChartWindow()
    sys.exit(app.exec_())
