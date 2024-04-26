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
from .custom_q_dialogs.error_dialog import ErrorDialog
from .custom_q_graphics_views.qGraphicsViewWithScene import QGraphicsViewWithScene
from .custom_q_graphics_views.inputImageQGraphicsView import InputImageQGraphicsView

logger = config.logger


class MainWindow(QMainWindow):
    """
    QMainWindow to set basic options and start chart detections
    """
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
        self.worker.error_signal.connect(self.open_error_dialog)
        self.worker_thread.start()

        self.showMaximized()
        logger.info(f"{self.__class__.__name__} inited")

    def contains_legend_changed(self):
        """
        Called when QRadioButton to select if chart contains legend or not is changed, enables input view to crop legend
        """
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

    def legend_has_cropped(self, pixmap: QPixmap):
        """
        Called when legend has cropped in input view

        Args:
            pixmap: cropped legend
        """
        contains = self.contains_legend.isChecked()
        if contains:
            self.crop_legend_label.setText("Kijelölt jelmagyarázat:")
            self.cropped_legend.setHidden(False)
            scaled_pixmap = pixmap.scaled(400, min(pixmap.height(), 500), Qt.KeepAspectRatio)

            self.cropped_legend.setPixmap(scaled_pixmap)
            self.legend_pixmap = pixmap

    def scan_legend(self):
        """
        Starts legend detections
        """
        self.legend_image_bgr = self.convert_pixmap_to_image(self.legend_pixmap)
        legend_position = self.input_image_view.crop_rect
        logger.info(f"Bounding rect of cropped legend: {legend_position}")
        chart_image_np = self.convert_pixmap_to_image(self.input_image_view.image)
        self.main_work_requested.emit(chart_image_np, self.legend_image_bgr, legend_position)

    @pyqtSlot()
    def set_loading_screen_on_input(self):
        """
        pyqtSlot to start loading screen on input view
        """
        self.input_image_view.start_loading_screen()

    @pyqtSlot()
    def set_loading_screen_on_output(self):
        """
        pyqtSlot to start loading screen on output view
        """
        self.output_image_view.start_loading_screen()

    def scan_chart(self):
        """
        Starts chart detections
        """
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
            self.main_work_requested.emit(chart_image_np, None, None)

    def export(self, extension):
        """
        Opens a QFileDialog to export generated chart es .pdf or .png

        Args:
            extension: .pdf or .png, target extension
        """
        dst = QFileDialog.getSaveFileName(self, "Save File",
                                          str(config.file_name) + "." + extension,
                                          "*." + extension)[0]
        if dst:
            copyfile(str(config.generated_charts_path / config.file_name) + "." + extension, dst)
        logger.info(f"{str(config.file_name)} \texported as \t{dst.split('/')[-1]}")

    def open_edit_window(self):
        """
        Sets options for EditWindow, closes the current and opens the EditWindow
        """
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
        """
        Closes the current window and opens the InputWindow to reselect the chart
        """
        self.close()
        logger.info(f"{self.__class__.__name__} closed")
        self.parent_window.showMaximized()

    def convert_pixmap_to_image(self, pixmap):
        """
        Converts QPixmap to np.ndarray

        Args:
            pixmap: QPixmap to convert
        """
        image = pixmap.toImage()
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        np_image = np.frombuffer(ptr, np.uint8).reshape(image.height(), image.width(), 4)
        converted_np_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2BGR)
        return converted_np_image

    def auto_straightening(self):
        """
        Straighten the image
        """
        self.set_loading_screen_on_input()
        self.rotate_button.setHidden(False)
        self.legend_group.setHidden(False)
        self.title_group.setHidden(False)
        self.scanButton.setHidden(False)
        chart_image_np = self.convert_pixmap_to_image(self.input_image_view.image)
        self.auto_straightening_signal.emit(chart_image_np)

    def rotate_right_by_90(self):
        """
        Rotates the input image by 90° if output of auto-straightening process over-rotated it
        """
        self.input_image_view.set_image(self.input_image_view.image.transformed(QTransform().rotate(90)))
        logger.info(f"Input chart image rotated by 90° on {self.__class__.__name__}")

    def open_error_dialog(self, error_list):
        """
        Opens error dialog

        Args:
            error_list: list containing the errors based on the raised Exceptions
        """
        dialog = ErrorDialog(error_list, self)
        dialog.exec_()
