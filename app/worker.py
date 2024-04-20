import logging
import os

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage
from pylatex.errors import PyLaTeXError

from app import main_char_detections, image_detections, to_latex
from config import config

DEFAULT_DENSITY = 300
logger = config.logger


class Worker(QObject):
    fname = pyqtSignal(str)

    # completed = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window

    @pyqtSlot(object, object, object)
    def create_chart(self, chart, legend, legend_position):
        logger.info("Chart creation started")
        logger.info(f"Contains legend: {legend is not None}")

        if legend is not None:
            try:
                self.window.legend_bars_data = image_detections.scan_legend(legend)
                main_char_detections.start_char_detections(chart, self.window.title_pos, True, False,
                                                           self.window.legend_bars_data, legend_position)
            except PyLaTeXError as pylatexError:
                logger.exception("An error occurred during latex file generation to grouped "
                                                     "chart, can't generate the pdf: %s", pylatexError)
            except Exception as e:
                logger.exception("An error occurred during legend detection, can't continue the process.")
        else:
            try:
                main_char_detections.start_char_detections(chart, self.window.title_pos, False, False, None, None)

            except PyLaTeXError as pylatexError:
                logger.exception("An error occurred during latex file generation to simple chart, "
                                        "can't generate the pdf: %s", pylatexError)

            except Exception:
                    logger.exception("An error occurred during chart detection, can't continue the detection process.")

        os.system(str(config.convert_pdf_to_png_bat_file_path)
                  + " "
                  + str(config.generated_charts_path / config.file_name)
                  + " "
                  + str(DEFAULT_DENSITY))

        self.window.output_image_view.set_generated_image.emit(
            QPixmap(str(config.generated_charts_path / config.file_name) + ".png")
            , None
            , None)
        self.window.generation_completed.emit()

    @pyqtSlot(object, object, object)
    def update_chart(self, color, legend, legend_position):
        try:
            if legend is not None:
                to_latex.prepare_data_for_update(self.window.chart_type, color, legend_position,
                                                 self.window.title_str, self.window.title_pos)
            else:
                to_latex.prepare_data_for_update(self.window.chart_type, color, None,
                                                 self.window.title_str, self.window.title_pos)
            logger.info("Update of chart finished successfully")

        except Exception as e:
            logger.exception("An error occurred during chart update: %s", e)

        # os.system(str(config.convert_pdf_to_png_bat_file_path + " " + config.file_name + "300"))

        os.system(str(config.convert_pdf_to_png_bat_file_path)
                  + " "
                  + str(config.generated_charts_path / config.file_name)
                  + " "
                  + str(DEFAULT_DENSITY))

        # self.window.output_image_view.set_generated_image.emit(QPixmap(config.file_name + ".png"))

        self.window.output_image_view.set_generated_image.emit(
            QPixmap(str(config.generated_charts_path / config.file_name) + ".png")
            , None
            , None)

    @pyqtSlot(object)
    def auto_straightening(self, chart):
        try:
            straightened_chart = main_char_detections.start_char_detections(chart.copy(), None, None, True, None, None)
            height, width, _ = straightened_chart.shape
            bytes_per_line = 3 * width
            straightened_chart_pixmap = QPixmap.fromImage(
                QImage(straightened_chart.data, width, height, bytes_per_line, QImage.Format_BGR888))
            self.window.input_image_view.set_generated_image.emit(straightened_chart_pixmap, None, None)

        except Exception:
            logging.exception("An error occurred during auto straightening.")
            self.window.error_label.setHidden(False)
            self.window.error_label.setText("Hiba történt az automatikus egyenesítés során.")
            self.window.input_image_view.set_generated_image.emit(
                QPixmap(str(config.resources_path / "corrupted_image_icon.png")), 200, 200)
            self.window.legend_group.setHidden(True)
            self.window.title_group.setHidden(True)
            self.window.scanButton.setHidden(True)
            # self.window.details_group.setHidden(True)
