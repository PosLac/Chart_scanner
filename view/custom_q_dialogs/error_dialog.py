from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from config import config

logger = config.logger


class ErrorDialog(QtWidgets.QDialog):
    """
    QDialog to open when Exception was raised and show errors
    """
    def __init__(self, error_list=None, parent=None):
        super(ErrorDialog, self).__init__(parent)

        if error_list is None:
            error_list = []

        self.setWindowTitle("Hiba")
        self.setModal(True)
        self.layout = QtWidgets.QVBoxLayout()
        self.message_label = QtWidgets.QLabel("\n".join(error_list), self)
        self.default_font = QFont()
        self.default_font.setPointSize(11)
        self.message_label.setFont(self.default_font)
        self.close_button = QtWidgets.QPushButton("Ok", self)
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.message_label)
        self.layout.addWidget(self.close_button, alignment=Qt.AlignCenter)
        self.setLayout(self.layout)
        logger.info(f"{self.__class__.__name__} inited")
