import faulthandler
import sys

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QApplication, QGridLayout

from inputImageView import InputImageView
from mainWindow import MainWindow
from viewWithScene import ViewWithScene


class InputChartWindow(QMainWindow):

    def __init__(self, parent=None):
        super(InputChartWindow, self).__init__(parent)
        uic.loadUi("inputChartWindow.ui", self)

        self.main_window = None

        self.chart = None

        # left_grid_layout
        self.left_grid_layout = self.findChild(QGridLayout, "left_grid_layout")
        self.input_image_view = self.findChild(InputImageView, "input_image_view")
        self.input_image_view.setScene(self.input_image_view.scene)
        self.input_image_view.cropped.connect(
            lambda: self.jump_to_scan_button.setHidden(False))
        self.left_grid_layout.addWidget(self.input_image_view, 1, 0, alignment=Qt.AlignHCenter)
        self.file_name_label = self.findChild(QLabel, "file_name")
        self.open_files_button = self.findChild(QPushButton, "open_files")
        self.open_files_button.clicked.connect(self.open_file)

        # right_grid_layout
        self.right_grid_layout = self.findChild(QGridLayout, "right_grid_layout")
        self.output_image_view = self.findChild(ViewWithScene, "cropped_chart_view")
        self.output_image_view.setScene(self.output_image_view.scene)
        self.input_image_view.cropped.connect(self.output_image_view.set_image)
        self.right_grid_layout.addWidget(self.output_image_view, 1, 0, alignment=Qt.AlignHCenter)
        self.jump_to_scan_button = self.findChild(QPushButton, "jump_to_scan")
        self.jump_to_scan_button.clicked.connect(self.jump_to_main_window)
        self.jump_to_scan_button.setHidden(True)
        self.load_without_crop_button = self.findChild(QPushButton, "load_without_crop")
        self.load_without_crop_button.clicked.connect(self.set_chart_to_view)
        self.load_without_crop_button.setHidden(True)
        self.output_chart = self.findChild(QLabel, "output_chart")

        self.file_name = None
        self.showMaximized()

    def open_file(self):
        formats = " ".join(["*.{}".format(fo.data().decode()) for fo in QImageReader.supportedImageFormats()])
        img_filter = "Images ({})".format(formats)
        self.file_name, _ = QFileDialog.getOpenFileName(None, "Open file", "", filter=img_filter)

        if self.file_name:
            self.file_name_label.setText(self.file_name.split('/')[-1])
            self.input_image_view.enable_crop = True
            self.input_image_view.clear_scene()
            self.chart = QPixmap(self.file_name)
            self.input_image_view.set_image(self.chart)
            self.input_image_view.file_name = self.file_name
            self.load_without_crop_button.setHidden(False)
            self.right_grid_layout.setRowStretch(2, 0)
            self.right_grid_layout.setRowStretch(3, 0)

    def jump_to_main_window(self):
        self.close()
        self.main_window = MainWindow(self)
        if self.output_image_view.image:
            self.main_window.input_image_view.set_image(self.output_image_view.image)

    def set_chart_to_view(self):
        self.output_image_view.set_image(self.chart)
        self.jump_to_scan_button.setHidden(False)


if __name__ == "__main__":
    faulthandler.enable()
    app = QApplication(sys.argv)
    inputWindow = InputChartWindow()
    sys.exit(app.exec_())
