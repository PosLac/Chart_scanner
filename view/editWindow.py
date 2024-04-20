import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QMovie, QFont
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QLineEdit, QPushButton, QLabel, QSpinBox, \
    QColorDialog, QGridLayout

from app import axis_detections, worker, image_detections
from config import config
from view.custom_q_graphics_views.qGraphicsViewWithScene import QGraphicsViewWithScene

logger = config.logger


class EditWindow(QMainWindow):
    edit_work_requested = pyqtSignal(object, object, object)
    generation_completed = pyqtSignal()

    def __init__(self, parent_window):
        super(EditWindow, self).__init__()
        uic.loadUi(str(config.ui_path / "editWindow.ui"), self)

        # variables
        self.input_chart = QPixmap(str(config.generated_charts_path / config.file_name))
        self.input_chart = self.input_chart.scaledToWidth(700)
        self.legend_position = None
        self.legend_image_bgr = None
        self.orientation = image_detections.orientation
        self.parent_window = parent_window
        self.spinner = QMovie(str(config.resources_path / "Spin-1s-200px.gif"))
        self.title_str = ""
        self.title_pos = 0
        self.bars_with_data = None
        self.bgr_colors = image_detections.colors
        self.updated_bgr_colors = {}
        self.default_font = QFont()
        self.default_font.setPointSize(12)
        self.error_list = []
        self.chart_type = image_detections.chart_type
        self.axis_types_with_ticks = axis_detections.axis_types_with_ticks

        # color_layout
        self.color_layout = self.findChild(QGridLayout, "color_layout")

        # title_layout
        self.above = self.findChild(QRadioButton, "above")
        self.below = self.findChild(QRadioButton, "below")
        self.no_title = self.findChild(QRadioButton, "no_title")
        self.title = self.findChild(QLineEdit, "title_text")
        self.title.setText(image_detections.chart_title)
        self.above.setChecked(self.parent_window.above.isChecked())
        self.below.setChecked(self.parent_window.below.isChecked())
        self.no_title.setChecked(self.parent_window.no_title.isChecked())

        # min_max_layout
        self.xMin = self.findChild(QSpinBox, "xMin")
        self.xMax = self.findChild(QSpinBox, "xMax")
        self.yMin = self.findChild(QSpinBox, "yMin")
        self.yMax = self.findChild(QSpinBox, "yMax")
        self.init_min_max_values()

        # bottom_layout
        self.error_label = self.findChild(QLabel, "error_label")
        self.update_button = self.findChild(QPushButton, "update_button")
        self.back_button = self.findChild(QPushButton, "back")
        self.update_button.clicked.connect(self.update_chart)
        self.back_button.clicked.connect(self.back_to_main)

        # output_layout
        self.output_image_view = self.findChild(QGraphicsViewWithScene, "output_view")
        self.output_image_view.setScene(self.output_image_view.scene)
        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        self.export_button_pdf.clicked.connect(lambda: self.parent_window.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.parent_window.export("png"))

        # workers
        self.worker = worker.Worker(self)
        self.worker_thread = QThread()
        self.worker.fname.connect(self.update)
        self.edit_work_requested.connect(self.worker.update_chart)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        # self.generation_completed.connect(lambda: print("Update done"))
        self.initColors()
        logger.info(f"{self.__class__.__name__} inited")

    def init_min_max_values(self):
        if self.axis_types_with_ticks["y_axis_type"] == "number":
            self.yMax.setHidden(False)
            self.yMin.setHidden(False)
            self.yMax.setValue(self.axis_types_with_ticks["y_axis_max"])
            self.yMin.setValue(self.axis_types_with_ticks["y_axis_min"])

        elif self.axis_types_with_ticks["y_axis_type"] == "text":
            self.yMax.setHidden(True)
            self.yMin.setHidden(True)

        if self.axis_types_with_ticks["x_axis_type"] == "number":
            self.xMax.setHidden(False)
            self.xMin.setHidden(False)
            self.xMax.setValue(self.axis_types_with_ticks["x_axis_max"])
            self.xMin.setValue(self.axis_types_with_ticks["x_axis_min"])

        elif self.axis_types_with_ticks["x_axis_type"] == "text":
            self.xMax.setHidden(True)
            self.xMin.setHidden(True)

    def set_min_max_values(self):
        if self.axis_types_with_ticks["y_axis_type"] == "number":
            self.axis_types_with_ticks["y_axis_max"] = self.yMax.value()
            self.axis_types_with_ticks["y_axis_min"] = self.yMin.value()

        if self.axis_types_with_ticks["x_axis_type"] == "number":
            self.axis_types_with_ticks["x_axis_max"] = self.xMax.value()
            self.axis_types_with_ticks["x_axis_min"] = self.xMin.value()

    def initColors(self):
        if isinstance(self.bgr_colors, dict):
            for i, (key, value) in enumerate(self.bgr_colors.items()):
                color_label = QLabel()
                color_label.setFixedSize(30, 30)
                color_label.setStyleSheet(f"background: rgb({', '.join(map(str, value[::-1]))})")
                color_label.setFont(self.default_font)

                group_text = QLineEdit(str(key))
                group_text.setFont(self.default_font)

                color_picker_button = QPushButton("Oszlop színének módosítása")
                color_picker_button.setFont(self.default_font)
                # color_picker_button.setStyleSheet("padding: 10px")
                color_picker_button.clicked.connect(
                    lambda _, color=color_label, text=group_text: self.open_color_picker(color,
                                                                                         text))
                self.updated_bgr_colors[group_text] = value

                self.color_layout.addWidget(group_text, i, 0)
                self.color_layout.addWidget(color_label, i, 1)
                self.color_layout.addWidget(color_picker_button, i, 2, 1, 1, Qt.AlignRight)
        else:
            color_label = QLabel()
            color_label.setFixedSize(30, 30)
            color_label.setStyleSheet(f"background: rgb({', '.join(map(str, self.bgr_colors[::-1]))})")
            color_label.setFont(self.default_font)

            color_picker_button = QPushButton("Oszlop színének módosítása")
            color_picker_button.setFont(self.default_font)
            # color_picker_button.setStyleSheet("padding: 10px")
            color_picker_button.clicked.connect(lambda _, color_param=color_label: self.open_color_picker(color_param))

            self.color_layout.addWidget(color_label, 0, 0, 1, 1, Qt.AlignRight)
            self.color_layout.addWidget(color_picker_button, 0, 1, 1, 1, Qt.AlignRight)

    def open_color_picker(self, color_label, color_text_label=None):
        color = QColorDialog.getColor()
        if color.isValid():
            # print(f"hexa: {color.name()}, rgb: {color.getRgb()}, {color.getRgb()[:3]}")
            color_label.setStyleSheet(f"background: rgb({', '.join(map(str, color.getRgb()[:3]))})")
            if color_text_label:
                self.updated_bgr_colors[color_text_label] = np.array(color.getRgb()[:3][::-1], np.uint8)
            else:
                self.bgr_colors = color.getRgb()[:3][::-1]

    @pyqtSlot()
    def set_loading_sceen(self):
        self.output_image_view.add_label()

    def set_title_data(self):
        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        if self.title.text():
            self.title_str = self.title.text()

    def update_chart(self):
        self.fill_error_list()
        self.set_title_data()
        if isinstance(self.bgr_colors, dict):
            self.set_groups_for_update()
        self.set_min_max_values()
        self.display_error_list()

        if len(self.error_list) == 0:
            logger.info("Update started")
            self.set_loading_sceen()
            self.edit_work_requested.emit(self.bgr_colors, self.legend_image_bgr, self.legend_position)
            logger.info("Update finished")

    def set_groups_for_update(self):
        self.bgr_colors = {}
        for group_text, color in self.updated_bgr_colors.items():
            if group_text.text() == "":
                self.error_list.append("Csoport neve nem lehet üres.")
            elif group_text.text() in self.bgr_colors:
                self.error_list.append(f"Csoport neve csak egyszer szerepelhet. ({group_text.text()})")
            else:
                self.bgr_colors[group_text.text()] = color

    def fill_error_list(self):
        self.error_list.clear()
        if not self.xMin.isHidden() and not self.xMax.isHidden() and self.xMin.value() > self.xMax.value():
            self.error_list.append("A x tengely maximum értéke nagyobb kell, hogy legyen, mint a minimum.")

        if not self.yMin.isHidden() and not self.yMax.isHidden() and self.yMin.value() > self.yMax.value():
            self.error_list.append("Az y tengely maximum értéke nagyobb kell, hogy legyen, mint a minimum.")

        if self.title.text() == "" and self.title_pos != 0:
            self.error_list.append("Amennyiben nem szeretne címet megadni, válassza ki a 'Nincs cím' opciót.")

    def display_error_list(self):
        self.error_label.setText("\n".join(self.error_list))

    def back_to_main(self):
        self.close()
        self.parent_window.showMaximized()
