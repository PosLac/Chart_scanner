import os

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap

import functions.image_detections as detects
import functions.to_latex as latex
from functions.main import main


class Worker(QObject):
    fname = pyqtSignal(str)
    completed = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window

    @pyqtSlot(str, object, object)
    def create_chart(self, name, legend, legend_position):
        print("Creation started")
        print(f"\tContains legend: {legend is not None}")

        self.fname.emit(name)

        if legend is not None:
            self.window.legend_bars_data = detects.scan_legend(legend)
            main(name, self.window.title_pos, True, self.window.legend_bars_data, legend_position)
        else:
            main(name, self.window.title_pos, False, None, None)
        os.system('pdf2png.bat tikzdraw 300')
        self.window.output_image_view.set_generated_image.emit(QPixmap("tikzdraw.png"))
        self.window.generation_completed.emit()
        print("Creation finished")

    @pyqtSlot(object, object, object, object)
    def update_chart(self, color, legend, legend_position, axis_types_with_ticks):
        if legend is not None:
            latex.prepare_data_for_update(self.window.orientation, self.window.chart_type, color, legend_position,
                                          self.window.title_str, self.window.title_pos)
        else:
            latex.prepare_data_for_update(self.window.orientation, self.window.chart_type, color, None,
                                          self.window.title_str, self.window.title_pos)

        print("OS SYSTEM")
        os.system('pdf2png.bat tikzdraw 300')
        print("OS SYSTEM DONE")
        print("Worker done")
        self.window.output_image_view.set_generated_image.emit(QPixmap("tikzdraw.png"))
        print("EditWindow")
        # self.completed.emit()
