import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

import view


if __name__ == "__main__":
    # Activates the virtual environment
    act = str(Path(__file__).resolve().parent / "szakdoga_env/Scripts/activate")
    os.system(act)

    app = QApplication(sys.argv)
    inputWindow = view.InputChartWindow()
    sys.exit(app.exec_())
