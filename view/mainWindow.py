from shutil import copyfile

import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap, QTransform
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QRadioButton, QGroupBox, \
    QGridLayout, QCheckBox

from app import worker
from config import config
from .editWindow import EditWindow
from .custom_q_dialog.error_dialog import ErrorDialog
from .custom_q_graphics_views.qGraphicsViewWithScene import QGraphicsViewWithScene
from .custom_q_graphics_views.inputImageQGraphicsView import InputImageQGraphicsView

logger = config.logger


class MainWindow(QMainWindow):
    main_work_requested = pyqtSignal(object, object, object)
    generation_completed = pyqtSignal()
    auto_straightening_signal = pyqtSignal(object)

    def __init__(self, parent_window):
        super(MainWindow, self).__init__()
        uic.loadUi(str(config.ui_path / "mainWindow.ui"), self)
        self.setWindowTitle("Diagram generálása")

        # variables
        self.legend_bars_data = None
        self.legend_pixmap = None
        self.legend_image_bgr = None
        self.parent_window = parent_window
        self.edit_window = None
        self.bars_with_data = None
        self.spinner = QMovie(str(config.resources_path / "Spin-1s-200px.gif"))

        # input_layout
        self.back_button = self.findChild(QPushButton, "back_button")
        self.back_button.clicked.connect(self.back_to_input_window)
        self.file_name_label = self.findChild(QLabel, "file_name")
        self.file_name_label.setText(parent_window.file_name_label.text())
        self.input_image_view = self.findChild(InputImageQGraphicsView, "input_image_view")
        self.input_image_view.setScene(self.input_image_view.scene)

        # details_group
        self.details_group = self.findChild(QGroupBox, "details_group")  # TODO szükséges?

        # legend_group
        self.legend_group = self.findChild(QGroupBox, "legend_group")
        self.crop_legend_label = self.findChild(QLabel, "crop_legend_label")
        self.crop_legend_label.setHidden(True)
        self.contains_legend = self.findChild(QCheckBox, "contains_legend")
        self.contains_legend.stateChanged.connect(self.contains_legend_changed)
        self.cropped_legend = self.findChild(QLabel, "cropped_legend")

        # rotate_group
        self.auto_straightening_button = self.findChild(QPushButton, "auto_straightening_button")
        self.auto_straightening_button.clicked.connect(self.auto_straightening)
        self.rotate_button = self.findChild(QPushButton, "rotate_right_by_90_button")
        self.rotate_button.clicked.connect(self.rotate_right_by_90)

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
        self.output_image_view = self.findChild(QGraphicsViewWithScene, "output_view")
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
        self.export_button_pdf.clicked.connect(lambda: self.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.export("png"))
        self.edit_button.clicked.connect(self.open_edit_window)
        self.scanButton.clicked.connect(self.scan_chart)

        # worker config
        self.worker = worker.Worker(self)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.main_work_requested.connect(self.worker.create_chart)
        self.auto_straightening_signal.connect(self.worker.auto_straightening)
        self.generation_completed.connect(lambda: self.export_edit_group.setHidden(False))
        self.worker.error_signal.connect(self.open_modal_dialog)
        self.worker_thread.start()

        self.showMaximized()
        logger.info(f"{self.__class__.__name__} inited")

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
            scaled_pixmap = pixmap.scaled(400, min(pixmap.height(), 500), Qt.KeepAspectRatio)

            self.cropped_legend.setPixmap(scaled_pixmap)
            self.legend_pixmap = pixmap

    def scan_legend(self):
        self.legend_image_bgr = self.convert_pixmap_to_image(self.legend_pixmap)
        legend_position = self.input_image_view.crop_rect
        logger.info(f"Bounding rect of cropped legend: {legend_position}")
        chart_image_np = self.convert_pixmap_to_image(self.input_image_view.image)
        self.main_work_requested.emit(chart_image_np, self.legend_image_bgr, legend_position)  # TODO logger

    @pyqtSlot()
    def set_loading_screen_on_input(self):
        self.input_image_view.add_label()

    @pyqtSlot()
    def set_loading_screen_on_output(self):
        self.output_image_view.add_label()

    def scan_chart(self):
        self.set_loading_screen_on_output()

        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        if self.input_image_view.crop_rect:
            self.scan_legend()
        else:
            chart_image_np = self.convert_pixmap_to_image(self.input_image_view.image)
            self.main_work_requested.emit(chart_image_np, None, None)  # TODO logger

    def export(self, extension):
        dst = QFileDialog.getSaveFileName(self, "Save File",
                                          str(config.file_name) + "." + extension,
                                          "*." + extension)[0]
        if dst:
            copyfile(str(config.generated_charts_path / config.file_name) + "." + extension, dst)
        logger.info(f"{str(config.file_name)} \texported as \t{dst.split('/')[-1]}")

    def open_edit_window(self):
        self.edit_window = EditWindow(self)
        self.edit_window.output_image_view.set_image(self.output_image_view.image)
        self.edit_window.legend_image_bgr = self.legend_image_bgr
        self.edit_window.legend_position = self.input_image_view.crop_rect
        self.edit_window.bars_with_data = self.bars_with_data
        self.edit_window.legend_bars_data = self.legend_bars_data
        self.close()
        logger.info(f"{self.__class__.__name__} closed")
        self.edit_window.showMaximized()

    def back_to_input_window(self):
        self.close()
        logger.info(f"{self.__class__.__name__} closed")
        self.parent_window.showMaximized()

    def convert_pixmap_to_image(self, pixmap):
        image = pixmap.toImage()
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        np_image = np.frombuffer(ptr, np.uint8).reshape(image.height(), image.width(), 4)
        converted_np_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2BGR)
        return converted_np_image

    def auto_straightening(self):
        self.set_loading_screen_on_input()
        self.rotate_button.setHidden(False)
        self.legend_group.setHidden(False)
        self.title_group.setHidden(False)
        self.scanButton.setHidden(False)
        chart_image_np = self.convert_pixmap_to_image(self.input_image_view.image)
        self.auto_straightening_signal.emit(chart_image_np) #TODO logger

    def rotate_right_by_90(self):
        self.input_image_view.set_image(self.input_image_view.image.transformed(QTransform().rotate(90)))
        logger.info(f"Input chart image rotated by 90° on {self.__class__.__name__}")

    def open_modal_dialog(self, error_list):
        dialog = ErrorDialog(error_list, self)
        dialog.exec_()
