import sys
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QApplication


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        self.button = self.findChild(QPushButton, "openFiles")
        self.label = self.findChild(QLabel, "fileName")
        self.chart = self.findChild(QLabel, "chart")
        self.button.clicked.connect(self.clicker)

        self.chart.setPixmap(QtGui.QPixmap("chart_stacked.png"))

        self.show()

    def clicker(self):
        # self.label.setText("You clicked")
        fname = QFileDialog.getOpenFileName(None, "Open file", "")
        self.label.setText(fname[0])
        self.chart.setPixmap(QtGui.QPixmap(fname[0]))



app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()