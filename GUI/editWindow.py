from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QLineEdit, QPushButton, QLabel, QCheckBox, QSpinBox, QColorDialog

from functions import image_detectations as detects
from functions.worker import Worker
from viewWithScene import ViewWithScene


class EditWindow(QMainWindow):
    edit_work_requested = pyqtSignal(str, object, object, object)
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
        self.simple_chart_bar_color = detects.simple_chart_bar_color  #todo beállítani alap színt
        self.title_str = ""
        self.title_pos = 0
        self.update_bool = False

        # color_layout
        self.color_picker_button = self.findChild(QPushButton, "color_picker_button")
        self.color_picker_button.clicked.connect(self.open_color_picker)
        self.color_label = self.findChild(QLabel, "color_label")
        self.color_label.setStyleSheet(f"background: rgb({', '.join(map(str, self.simple_chart_bar_color))})")

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

        self.generation_completed.connect(lambda: print("update done"))

        print("inited")
        # self.showMaximized()

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print(f"hexa: {color.name()}, rgb: {color.getRgb()}, {color.getRgb()[:3]}")
            self.simple_chart_bar_color = color.getRgb()[:3]
            self.color_label.setStyleSheet(f"background: rgb({', '.join(map(str, self.simple_chart_bar_color))})")

    # def workerStarted(self, name, legend, legend_position):
    #     print("editWindow worker started")
    #     self.worker.update_chart(name, self.simple_chart_bar_color, legend, legend_position)

    def minMax_toggle(self, val):
        min_max = self.findChild(QSpinBox, val)
        min_max.setEnabled(not min_max.isEnabled())
        if not min_max.isEnabled():
            spinbox = self.findChild(QSpinBox, val)
            spinbox.setValue(0)

    @pyqtSlot()
    def set_loading_sceen(self):
        self.output_image_view.add_label()

    def update_chart(self):
        print("Update start")
        self.set_loading_sceen()
        error_list = ""
        self.update_bool = True
        self.xMin_en = self.xMin_check.isChecked()
        self.xMax_en = self.xMax_check.isChecked()
        self.yMin_en = self.yMin_check.isChecked()
        self.yMax_en = self.yMax_check.isChecked()

        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        if self.title.text() == "" and self.title_pos != 0:
            error_list = error_list + "\n Amennyiben nem szeretne címet megadni, válassza ki a 'Nincs cím' opciót."
            self.error_label.setText(error_list)

        if self.title.text():
            self.title_str = self.title.text()
            print(self.title_str)

        if (self.xMin_en and self.xMax_en and self.xMin.value() > self.xMax.value()) or \
                (self.yMin_en and self.yMax_en and self.yMin.value() > self.yMax.value()):
            error_list = error_list + "\n A maximum értéke nagyobb kell, hogy legyen, mint a minimum."
            self.error_label.setText(error_list)

        else:
            # self.loaded_chart.setPixmap(QPixmap())
            # self.loaded_chart.setMovie(self.spinner)
            self.spinner.start()
            self.minMax_array = [("xmin", self.xMin.value(), self.xMin_en), ("xmax", self.xMax.value(), self.xMax_en),
                                 ("ymin", self.yMin.value(), self.yMin_en), ("ymax", self.yMax.value(), self.yMax_en)]
            self.edit_work_requested.emit("", self.simple_chart_bar_color, self.legend_image_bgr, self.legend_position)
        print("Update finished")

    def back_to_main(self):
        self.close()
        self.parent_window.showMaximized()
