import os

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap

import functions.image_detectations as detects
import functions.to_latex as latex
from functions.main import main


class Worker(QObject):
    fname = pyqtSignal(str)
    completed = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window
        # self.window.output_image_view.image_setting_completed.connect(self.window.generation_completed)
        # self.chart = pyqtSignal(QPixmap)

    @pyqtSlot(str, object, object)
    def create_chart(self, name, legend, legend_position):
        print("Creation started")
        print(f"\tContains legend: {legend is not None}")

        self.fname.emit(name)

        if legend is not None:  # todo Jelmagyazázat beolvasása gomb is elindítja ez egészet
            # main(name, self.window.title_pos, legend, legend_position)
            self.window.legend_bars_data = detects.scan_legend(legend)
            main(name, self.window.title_pos, True, self.window.legend_bars_data, legend_position)
        else:
            # self.window.bars_with_colors = detects.merge_colors(detects.detect_colors(edits.resized_color, edits.elements, edits.bars_with_labels))
            main(name, self.window.title_pos, False, None, None)

        # if name:
        #     print(name)
        #     # self.window.output_image_view.set_image(QPixmap())
        #     # self.window.output_image_view.setMovie(self.window.spinner)
        #     # self.window.spinner.start()
        #     self.fname.emit(name)
        #     main(name, self.window.title_pos)

        # if update:
        #     latex(self.window.edit_window.update_bool, self.window.edit_window.orientation,
        #           self.window.edit_window.ratios, self.window.edit_window.minMax_array,
        #           self.window.edit_window.title_str, self.window.edit_window.title_pos)
        #     print("latex")
        os.system('pdf2png.bat tikzdraw 300')
        # output_chart = QPixmap("tikzdraw.png")
        # output_chart = output_chart.scaledToWidth(700)
        self.window.output_image_view.set_generated_image.emit(QPixmap("tikzdraw.png"))
        self.window.generation_completed.emit()
        print("Creation finished")

    @pyqtSlot(str, object, object, object)
    def update_chart(self, name, color, legend, legend_position):
        print("update_chart started")

        # if name:
        #     print(name)
        #     # self.window.output_image_view.set_image(QPixmap())
        #     # self.window.output_image_view.setMovie(self.window.spinner)
        #     # self.window.spinner.start()
        #     self.fname.emit(name)
        #     main(name, self.window.title_pos)

        # latex.latex(self.window.update_bool, self.window.orientation,
        #       self.window.ratios, self.window.minMax_array,
        #       self.window.title_str, self.window.title_pos)

        if legend is not None:
            latex.prepare_data_for_update(self.window.orientation, True, self.window.ratios, color, self.window.legend_bars_data, legend_position,
                                          self.window.minMax_array, self.window.title_str, self.window.title_pos)
        else:
            latex.prepare_data_for_update(self.window.orientation, False, self.window.ratios, color, None, None,
                                          self.window.minMax_array, self.window.title_str, self.window.title_pos)

        print("OS SYSTEM")
        os.system('pdf2png.bat tikzdraw 300')
        print("OS SYSTEM DONE")
        output_chart = QPixmap("tikzdraw.png")
        output_chart = output_chart.scaledToWidth(700)
        print("Worker done")
        self.window.output_image_view.set_generated_image.emit(QPixmap("tikzdraw.png"))
        print("EditWindow")
        # self.completed.emit()
