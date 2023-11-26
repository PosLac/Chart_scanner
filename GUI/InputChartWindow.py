import sys
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QApplication, QGridLayout

from inputImageView import InputImageView
from GUI.loadgui import MainWindow
from viewWithScene import ViewWithScene


class InputChartWindow(QMainWindow):
    cropped = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super(InputChartWindow, self).__init__(parent)
        uic.loadUi("InputChartWindow.ui", self)

        self.main_window = None

        self.left_grid_layout = self.findChild(QGridLayout, "left_grid_layout")
        self.right_grid_layout = self.findChild(QGridLayout, "right_grid_layout")

        self.open_files_button = self.findChild(QPushButton, "open_files")
        self.jump_to_scan_button = self.findChild(QPushButton, "jump_to_scan_button")

        self.label = self.findChild(QLabel, "file_name")
        self.input_image = self.findChild(QLabel, "input_image")
        self.output_chart = self.findChild(QLabel, "output_chart")

        self.open_files_button.clicked.connect(self.open_file)
        self.jump_to_scan_button.clicked.connect(self.jump_to_scan)

        # self.input_image_view = InputImageView()
        # self.cropped_chart_view = ViewWithScene()

        self.input_image_view = self.findChild(InputImageView, "input_image_view")
        self.cropped_chart_view = self.findChild(ViewWithScene, "cropped_chart_view")

        self.input_image_view.cropped.connect(self.cropped_chart_view.set_image)
        self.input_image_view.setScene(self.input_image_view.scene())
        self.cropped_chart_view.setScene(self.cropped_chart_view.scene())

        self.left_grid_layout.addWidget(self.input_image_view, 1, 0)
        self.right_grid_layout.addWidget(self.cropped_chart_view, 1, 0)

        self.showMaximized()

    def open_file(self):
        # todo drag&drop?
        formats = " ".join(["*.{}".format(fo.data().decode()) for fo in QImageReader.supportedImageFormats()])
        img_filter = "Images ({})".format(formats)
        file_name, _ = QFileDialog.getOpenFileName(None, "Open file", "", filter=img_filter)

        if file_name:
            self.label.setText(file_name.split('/')[-1])
            self.input_image_view.clear_scene()
            input_chart = QPixmap(file_name)
            # input_chart = input_chart.scaledToWidth(700)
            self.input_image_view.set_image(input_chart)
            self.input_image_view.calculate_scales()

    def jump_to_scan(self):
        self.main_window = MainWindow()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    inputWindow = InputChartWindow()
    sys.exit(app.exec_())
