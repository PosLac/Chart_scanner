import sys

from PyQt5.QtWidgets import QApplication

import view

if __name__ == "__main__":
    app = QApplication(sys.argv)
    inputWindow = view.InputChartWindow()
    sys.exit(app.exec_())
