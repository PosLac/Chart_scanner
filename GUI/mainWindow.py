from shutil import copyfile
import sys

import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap, QImage
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QApplication, QRadioButton, QGroupBox, \
    QGridLayout, QCheckBox

from inputImageView import InputImageView
from functions import worker
from viewWithScene import ViewWithScene
from editWindow import EditWindow


class MainWindow(QMainWindow):
    work_requested = pyqtSignal(str, bool, object, list)

    def __init__(self, parent_window):
        super(MainWindow, self).__init__()
        self.parent_window = parent_window

        uic.loadUi("mainWindow.ui", self)
        self.edit_window = None

        # input_layout
        self.back_button = self.findChild(QPushButton, "back_button")
        self.file_name_label = self.findChild(QLabel, "file_name")
        self.file_name_label.setText(parent_window.file_name_label.text())
        self.input_image_view = self.findChild(InputImageView, "input_image_view")
        self.input_image_view.setScene(self.input_image_view.scene())
        self.back_button.clicked.connect(self.back_to_input_window)

        # legend_group
        self.crop_legend_label = self.findChild(QLabel, "crop_legend_label")
        self.crop_legend_label.setHidden(True)
        self.contains_legend = self.findChild(QCheckBox, "contains_legend")
        self.contains_legend.stateChanged.connect(self.contains_legend_changed)
        # self.jump_to_crop_legend.setHidden(True)
        # self.jump_to_crop_legend = self.findChild(QPushButton, "jump_to_crop_legend")
        # self.contains_legend.stateChanged.connect(lambda: self.jump_to_crop_legend.setHidden(not self.contains_legend.isChecked()))

        # title_group
        self.title_group = self.findChild(QGroupBox, "title_group")
        self.title_pos = 0
        self.above = self.findChild(QRadioButton, "above")
        self.above.setChecked(False)
        self.below = self.findChild(QRadioButton, "below")
        self.below.setChecked(False)
        self.no_title = self.findChild(QRadioButton, "no_title")
        self.no_title.setChecked(True)

        # output_layout
        self.output_title = self.findChild(QLabel, "output_title")
        self.output_layout = self.findChild(QGridLayout, "output_layout")
        self.output_image_view = self.findChild(ViewWithScene, "output_view")
        self.output_image_view.setScene(self.output_image_view.scene())
        self.input_image_view.cropped.connect(self.output_image_view.set_image)
        self.input_image_view.cropped.connect(self.legend_has_cropped)
        self.output_layout.addWidget(self.output_image_view, 1, 0)

        self.crop_image_button = self.findChild(QPushButton, "crop_image")
        self.scanButton = self.findChild(QPushButton, "scan")
        self.export_edit_group = self.findChild(QGroupBox, "export_edit_group")
        self.export_edit_group.setHidden(True)
        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        self.edit_button = self.findChild(QPushButton, "edit_button")
        self.spinner = QMovie("Spin-1s-200px.gif")
        self.export_button_pdf.clicked.connect(lambda: self.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.export("png"))
        self.edit_button.clicked.connect(self.open_edit_window)
        self.scanButton.clicked.connect(self.scan_chart)

        # worker config
        self.worker = worker.Worker(self)
        self.worker_thread = QThread()
        self.worker.fname.connect(self.update)
        # self.worker.completed.connect(self.worker_thread.exit)
        self.worker.completed.connect(self.workerCompleted)
        self.work_requested.connect(self.workerStarted)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.read_legend_button = self.findChild(QPushButton, "read_legend")
        self.read_legend_button.setHidden(True)
        self.read_legend_button.clicked.connect(self.scan_legend)

        self.showMaximized()

    def workerStarted(self, str, bool, legend, legend_position):
        print("mainWindow worker started")
        self.worker.do_work(str, bool, legend, legend_position)

    def workerCompleted(self):
        print("mainWindow worker completed")
        self.worker_thread.exit()

    def contains_legend_changed(self):
        contains = self.contains_legend.isChecked()
        self.crop_legend_label.setHidden(not contains)
        self.input_image_view.enable_crop = contains
        self.output_title.setText("Jelmagyarázat" if contains else "Beolvasott diagram")
        self.read_legend_button.setHidden(True)

        if not contains:
            self.input_image_view.clear_scene()
            self.input_image_view.set_image(self.parent_window.output_image_view.image)
            self.output_image_view.scene().clear()
            self.output_image_view.pixmap_item = self.output_image_view.scene().addPixmap(QPixmap())

    def legend_has_cropped(self):
        contains = self.contains_legend.isChecked()
        if contains:
            self.read_legend_button.setHidden(False)

    def set_legend_data(self):
        self.output_image_view.set_image(self.input_image_view.result)

    def scan_legend(self):
        legend_image = self.output_image_view.image.toImage()
        ptr = legend_image.bits()
        ptr.setsize(legend_image.byteCount())
        legend_image_np = np.frombuffer(ptr, np.uint8).reshape(legend_image.height(), legend_image.width(), 4)

        # change color to white where alpha channel is 0
        legend_image_np[legend_image_np[:, :, 3] == 0] = [255, 255, 255, 255]
        legend_image_bgr = cv2.cvtColor(legend_image_np, cv2.COLOR_BGRA2BGR)

        # cv2.imshow("legend_image_bgr", legend_image_bgr)
        legend_position = self.input_image_view.click_pos_array
        self.work_requested.emit(self.parent_window.file_name, False, legend_image_bgr, legend_position)

    def scan_chart(self):
        global fname
        fname = self.parent_window.file_name
        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        print("fname", fname)
        self.work_requested.emit(fname, False, None, [])
        self.spinner.start()

    def export(self, type):
        input_file = "tikzdraw." + type
        dst = QFileDialog.getSaveFileName(self, 'Save File', 'tikzdraw.' + type, "*." + type)[0]
        if dst:
            copyfile(input_file, dst)
        print("copy done")

    def open_edit_window(self):
        self.close()
        self.edit_window = EditWindow(self)

    def back_to_input_window(self):
        self.close()
        self.parent_window.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    inputWindow = MainWindow(None)
    sys.exit(app.exec_())