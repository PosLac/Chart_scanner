import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, QRect, Qt
from PyQt5.QtGui import QPixmap, QMovie, QFont
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QLineEdit, QPushButton, QLabel, QCheckBox, QSpinBox, \
    QColorDialog, QGridLayout

from functions import image_detections as detects, color_detections, image_detections
from functions.worker import Worker
from viewWithScene import ViewWithScene


class EditWindow(QMainWindow):
    edit_work_requested = pyqtSignal(object, object, object)
    generation_completed = pyqtSignal()

    def __init__(self, parent_window):
        super(EditWindow, self).__init__()
        uic.loadUi("editWindow.ui", self)

        # variables
        self.input_chart = QPixmap("tikzdraw.png")
        self.input_chart = self.input_chart.scaledToWidth(700)
        self.legend_position = None
        self.legend_image_bgr = None
        self.minMax_array = None
        self.orientation = detects.orientation
        self.parent_window = parent_window
        self.ratios = detects.ratios
        self.spinner = QMovie("Spin-1s-200px.gif")
        self.title_str = ""
        self.title_pos = 0
        self.bars_with_data = None
        self.colors = image_detections.colors
        self.updated_colors = {}
        self.default_font = QFont()
        self.default_font.setPointSize(12)
        self.error_list = []

        # color_layout
        self.color_layout = self.findChild(QGridLayout, "color_layout")

        # title_layout
        self.above = self.findChild(QRadioButton, "above")
        self.below = self.findChild(QRadioButton, "below")
        self.no_title = self.findChild(QRadioButton, "no_title")
        self.title = self.findChild(QLineEdit, "title_text")
        self.title.setText(detects.chart_title)
        self.above.setChecked(self.parent_window.above.isChecked())
        self.below.setChecked(self.parent_window.below.isChecked())
        self.no_title.setChecked(self.parent_window.no_title.isChecked())

        # min_max_layout
        self.xMin_check = self.findChild(QCheckBox, "xMin_check")
        self.xMax_check = self.findChild(QCheckBox, "xMax_check")
        self.yMin_check = self.findChild(QCheckBox, "yMin_check")
        self.yMax_check = self.findChild(QCheckBox, "yMax_check")
        self.xMin = self.findChild(QSpinBox, "xMin")
        self.xMax = self.findChild(QSpinBox, "xMax")
        self.yMin = self.findChild(QSpinBox, "yMin")
        self.yMax = self.findChild(QSpinBox, "yMax")
        self.xMin_en = self.xMin_check.isChecked()
        self.xMax_en = self.xMax_check.isChecked()
        self.yMin_en = self.yMin_check.isChecked()
        self.yMax_en = self.yMax_check.isChecked()
        self.xMin_check.stateChanged.connect(lambda: self.minMax_toggle("xMin"))
        self.xMax_check.stateChanged.connect(lambda: self.minMax_toggle("xMax"))
        self.yMin_check.stateChanged.connect(lambda: self.minMax_toggle("yMin"))
        self.yMax_check.stateChanged.connect(lambda: self.minMax_toggle("yMax"))

        # bottom_layout
        self.error_label = self.findChild(QLabel, "error_label")
        self.update_button = self.findChild(QPushButton, "update_button")
        self.back_button = self.findChild(QPushButton, "back")
        self.update_button.clicked.connect(self.update_chart)
        self.back_button.clicked.connect(self.back_to_main)

        # output_layout
        self.output_image_view = self.findChild(ViewWithScene, "output_view")
        self.output_image_view.setScene(self.output_image_view.scene)
        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        self.export_button_pdf.clicked.connect(lambda: self.parent_window.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.parent_window.export("png"))

        # workers
        self.worker = Worker(self)
        self.worker_thread = QThread()
        self.worker.fname.connect(self.update)
        self.edit_work_requested.connect(self.worker.update_chart)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.generation_completed.connect(lambda: print("Update done"))
        self.initColors()
        print("inited")
        # self.showMaximized()

    def initColors(self):
        if isinstance(self.colors, dict):
            for i, (key, value) in enumerate(self.colors.items()):
                color_label = QLabel()
                color_label.setFixedSize(30, 30)
                color_label.setStyleSheet(f"background: rgb({', '.join(map(str, value))})")
                color_label.setFont(self.default_font)

                group_text = QLineEdit(str(key))
                group_text.setFont(self.default_font)

                color_picker_button = QPushButton("Oszlop színének módosítása")
                color_picker_button.setFont(self.default_font)
                # color_picker_button.setStyleSheet("padding: 10px")
                color_picker_button.clicked.connect(
                    lambda _, color=color_label, text=group_text: self.open_color_picker(color,
                                                                                         text))
                self.updated_colors[group_text] = value

                self.color_layout.addWidget(group_text, i, 0)
                self.color_layout.addWidget(color_label, i, 1)
                self.color_layout.addWidget(color_picker_button, i, 2, 1, 1, Qt.AlignRight)
        else:
            color_label = QLabel()
            color_label.setFixedSize(30, 30)
            color_label.setStyleSheet(f"background: rgb({', '.join(map(str, self.colors))})")
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
            print(f"hexa: {color.name()}, rgb: {color.getRgb()}, {color.getRgb()[:3]}")
            color_label.setStyleSheet(f"background: rgb({', '.join(map(str, color.getRgb()[:3]))})")
            if color_text_label:
                self.updated_colors[color_text_label] = np.array(color.getRgb()[:3], np.uint8)
            else:
                self.colors = color.getRgb()[:3]

    def minMax_toggle(self, val):
        min_max = self.findChild(QSpinBox, val)
        min_max.setEnabled(not min_max.isEnabled())
        if not min_max.isEnabled():
            spinbox = self.findChild(QSpinBox, val)
            spinbox.setValue(0)

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

    def set_min_max_array(self):
        self.xMin_en = self.xMin_check.isChecked()
        self.xMax_en = self.xMax_check.isChecked()
        self.yMin_en = self.yMin_check.isChecked()
        self.yMax_en = self.yMax_check.isChecked()
        self.minMax_array = [("xmin", self.xMin.value(), self.xMin_en), ("xmax", self.xMax.value(), self.xMax_en),
                             ("ymin", self.yMin.value(), self.yMin_en), ("ymax", self.yMax.value(), self.yMax_en)]

    def update_chart(self):
        self.fill_error_list()
        self.set_title_data()
        if isinstance(self.colors, dict):
            self.set_groups_for_update()
        self.set_min_max_array()
        self.display_error_list()

        if len(self.error_list) == 0:
            print("Update start")
            self.set_loading_sceen()
            self.edit_work_requested.emit(self.colors, self.legend_image_bgr, self.legend_position)
            print("Update finished")

    def set_groups_for_update(self):
        self.colors = {}
        for group_text, color in self.updated_colors.items():
            if group_text.text() == "":
                self.error_list.append("Csoport neve nem lehet üres.")
            elif group_text.text() in self.colors:
                self.error_list.append(f"Csoport neve csak egyszer szerepelhet. ({group_text.text()})")
            else:
                self.colors[group_text.text()] = color

    def fill_error_list(self):
        self.error_list.clear()
        if (self.xMin_en and self.xMax_en and self.xMin.value() > self.xMax.value()) or \
                (self.yMin_en and self.yMax_en and self.yMin.value() > self.yMax.value()):
            self.error_list.append("A maximum értéke nagyobb kell, hogy legyen, mint a minimum.")

        if self.title.text() == "" and self.title_pos != 0:
            self.error_list.append("Amennyiben nem szeretne címet megadni, válassza ki a 'Nincs cím' opciót.")

    def display_error_list(self):
        self.error_label.setText("\n".join(self.error_list))

    def back_to_main(self):
        self.close()
        self.parent_window.showMaximized()
