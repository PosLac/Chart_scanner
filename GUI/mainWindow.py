from shutil import copyfile

import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QRadioButton, QGroupBox, \
    QGridLayout, QCheckBox

from editWindow import EditWindow
from functions import worker
from inputImageView import InputImageView
from viewWithScene import ViewWithScene


class MainWindow(QMainWindow):
    main_work_requested = pyqtSignal(str, object, object)
    generation_completed = pyqtSignal()

    def __init__(self, parent_window):
        super(MainWindow, self).__init__()
        self.legend_bars_data = None
        self.legend_pixmap = None
        self.legend_image_bgr = None
        self.parent_window = parent_window

        uic.loadUi("mainWindow.ui", self)
        self.edit_window = None
        self.bars_with_data = None

        # input_layout
        self.back_button = self.findChild(QPushButton, "back_button")
        self.file_name_label = self.findChild(QLabel, "file_name")
        self.file_name_label.setText(parent_window.file_name_label.text())
        self.input_image_view = self.findChild(InputImageView, "input_image_view")
        self.input_image_view.setScene(self.input_image_view.scene)
        self.back_button.clicked.connect(self.back_to_input_window)

        # legend_group
        self.crop_legend_label = self.findChild(QLabel, "crop_legend_label")
        self.crop_legend_label.setHidden(True)
        self.contains_legend = self.findChild(QCheckBox, "contains_legend")
        self.contains_legend.stateChanged.connect(self.contains_legend_changed)
        self.cropped_legend = self.findChild(QLabel, "cropped_legend")

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
        self.output_image_view.setScene(self.output_image_view.scene)
        self.input_image_view.cropped.connect(self.legend_has_cropped)
        self.output_layout.addWidget(self.output_image_view, 1, 0, alignment=Qt.AlignHCenter)

        self.crop_image_button = self.findChild(QPushButton, "crop_image")
        self.scanButton = self.findChild(QPushButton, "scan")
        self.export_edit_group = self.findChild(QGroupBox, "export_edit_group")
        self.export_edit_group.setHidden(True)
        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        self.edit_button = self.findChild(QPushButton, "edit_button")
        self.spinner = QMovie("Others/Spin-1s-200px.gif")
        self.export_button_pdf.clicked.connect(lambda: self.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.export("png"))
        self.edit_button.clicked.connect(self.open_edit_window)
        self.scanButton.clicked.connect(self.scan_chart)

        # worker config
        self.worker = worker.Worker(self)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.fname.connect(self.update)
        self.worker.completed.connect(self.workerCompleted)
        self.main_work_requested.connect(self.worker.create_chart)
        self.generation_completed.connect(lambda: self.export_edit_group.setHidden(False))
        self.worker_thread.start()

        self.showMaximized()

    def workerCompleted(self):
        print("mainWindow worker completed")

        self.worker_thread.exit()

    def contains_legend_changed(self):
        contains = self.contains_legend.isChecked()
        self.crop_legend_label.setHidden(not contains)
        self.cropped_legend.setHidden(not contains)
        self.input_image_view.enable_crop = contains

        if not contains:
            self.input_image_view.clear_scene()
            self.input_image_view.set_image(self.parent_window.output_image_view.image)
            self.cropped_legend.setPixmap(QPixmap())
            self.crop_legend_label.setText("Jelölje ki a diagramon a jelmagyarázatot tartalmazó részt")
            self.input_image_view.crop_rect = None

    def legend_has_cropped(self, pixmap):
        contains = self.contains_legend.isChecked()
        if contains:
            self.crop_legend_label.setText("Kijelölt jelmagyarázat:")
            self.cropped_legend.setHidden(False)
            scaled_pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
            self.cropped_legend.setPixmap(scaled_pixmap)
            self.legend_pixmap = pixmap

    def scan_legend(self):
        legend_image = self.legend_pixmap.toImage()
        ptr = legend_image.bits()
        ptr.setsize(legend_image.byteCount())
        legend_image_np = np.frombuffer(ptr, np.uint8).reshape(legend_image.height(), legend_image.width(), 4)

        # change color to white where alpha channel is 0
        legend_image_np[legend_image_np[:, :, 3] == 0] = [255, 255, 255, 255]
        self.legend_image_bgr = cv2.cvtColor(legend_image_np, cv2.COLOR_BGRA2BGR)

        legend_position = self.input_image_view.crop_rect
        print(f"\tLegend_position: {legend_position}")

        self.main_work_requested.emit(self.parent_window.file_name, self.legend_image_bgr, legend_position)

    @pyqtSlot()
    def set_loading_sceen(self):
        self.output_image_view.add_label()

    def scan_chart(self):
        self.set_loading_sceen()

        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        print(f"File name: {self.parent_window.file_name}")

        if self.input_image_view.crop_rect:
            self.scan_legend()
        else:
            self.main_work_requested.emit(self.parent_window.file_name, None, None)

    def export(self, chart_type):
        input_file = "tikzdraw." + chart_type
        dst = QFileDialog.getSaveFileName(self, 'Save File', 'tikzdraw.' + chart_type, "*." + chart_type)[0]
        if dst:
            copyfile(input_file, dst)
        print("Copy done")

    def open_edit_window(self):
        self.edit_window = EditWindow(self)
        self.edit_window.output_image_view.set_image(self.output_image_view.image)
        self.edit_window.legend_image_bgr = self.legend_image_bgr
        self.edit_window.legend_position = self.input_image_view.crop_rect
        self.edit_window.bars_with_data = self.bars_with_data
        self.edit_window.legend_bars_data = self.legend_bars_data
        self.close()
        self.edit_window.showMaximized()

    def back_to_input_window(self):
        self.close()
        self.parent_window.showMaximized()
