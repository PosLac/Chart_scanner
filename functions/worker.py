import os

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot as Slot
from PyQt5.QtGui import QPixmap

import functions.image_detectations as detectations
from functions.main import main
from functions.to_latex import latex


class Worker(QObject):
    fname = pyqtSignal(str)
    completed = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.chart = pyqtSignal(QPixmap)

    @Slot(str, bool)
    def do_work(self, name, update, legend, legend_position):
        print("do_work")
        print(f"Contains legend: {legend is not None}")

        if legend is not None:
            # main(name, self.window.title_pos, legend, legend_position)
            bars_with_texts = detectations.scan_legend(legend)
            main(name, self.window.title_pos, True, bars_with_texts, legend_position)
        else:
            main(name, self.window.title_pos, False, None, None)

        # if name:
        #     print(name)
        #     # self.window.output_image_view.set_image(QPixmap())
        #     # self.window.output_image_view.setMovie(self.window.spinner)
        #     # self.window.spinner.start()
        #     self.fname.emit(name)
        #     main(name, self.window.title_pos)

        if update:
            latex(self.window.edit_window.update_bool, self.window.edit_window.orientation,
                  self.window.edit_window.ratios, self.window.edit_window.minMax_array,
                  self.window.edit_window.title_str, self.window.edit_window.title_pos)
            print("latex")
        print("OS SYSTEM")
        os.system('pdf2png.bat tikzdraw 300')
        print("OS SYSTEM DONE")
        output_chart = QPixmap("tikzdraw.png")
        output_chart = output_chart.scaledToWidth(700)
        print("worker done")
        if name:
            self.window.output_image_view.set_image(output_chart)
            self.window.export_edit_group.setHidden(False)
            print("MainWindow")
        else:
            self.window.edit_window.loaded_chart.set_image(output_chart)
            print("EditWindow")
        self.completed.emit()
