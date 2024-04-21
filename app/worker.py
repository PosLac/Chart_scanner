import logging
import os
import random

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage
from pylatex.errors import PyLaTeXError

from app import main_char_detections, image_detections, to_latex
from config import config

DEFAULT_DENSITY = 300
logger = config.logger


class Worker(QObject):
    error_signal = pyqtSignal(list)

    # completed = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window

    @pyqtSlot(object, object, object)
    def create_chart(self, chart, legend, legend_position):
        logger.info("Chart creation started")
        logger.info(f"Contains legend: {legend is not None}")
        try:
            if legend is not None:
                self.window.legend_bars_data = image_detections.scan_legend(legend)
                if len(self.window.legend_bars_data) == 0:
                    logger.exception("Can't detect bars on legend, can't continue the detection process.")
                    raise Exception(
                        "Nem lehet beolvasni a kijelölt jelmagyarázatot, próbálkozzon minél pontosabb kijelöléssel.")
                else:
                    main_char_detections.start_char_detections(chart, self.window.title_pos, True, False,
                                                               self.window.legend_bars_data, legend_position)
            else:
                logger.info("Simple chart type detected")
                main_char_detections.start_char_detections(chart, self.window.title_pos, False, False, None, None)

            os.system(str(config.convert_pdf_to_png_bat_file_path)
                      + " "
                      + str(config.generated_charts_path / config.file_name)
                      + " "
                      + str(DEFAULT_DENSITY))

            self.window.output_image_view.set_generated_image.emit(
                QPixmap(str(config.generated_charts_path / config.file_name) + ".png")
                , None
                , None)

        except PyLaTeXError as pylatexError:
            logger.exception(
                "An error occurred during running of the latex file, can't generate the pdf: %s",
                pylatexError)

            self.error_signal.emit([f"Hiba történt a generált latex fájl futtatása során: {pylatexError}",
                                    f"A latex fájlt a {str(config.generated_charts_path / config.file_name)}.tex útvonalon található."])
            self.window.output_image_view.set_error_image_signal.emit()

        except Exception as e:
            logger.exception("An error occurred during chart detection, can't continue the process: %s", e)
            self.error_signal.emit([f"Hiba történt a diagram beolvasása során: {e}"])
            self.window.output_image_view.set_error_image_signal.emit()

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

        except PyLaTeXError as pylatexError:
            logger.exception(
                "An error occurred during running of the latex file, can't generate the pdf: %s",
                pylatexError)

            self.error_signal.emit([f"Hiba történt a generált latex fájl futtatása során: {pylatexError}",
                                    f"A latex fájlt a {str(config.generated_charts_path / config.file_name)}.tex útvonalon található."])

        except Exception as e:
            logger.exception("An error occurred during chart update, can't continue the proces: %s", e)
            self.error_signal.emit([f"Hiba történt a diagram módosítása során: {e}"])

        os.system(str(config.convert_pdf_to_png_bat_file_path)
                  + " "
                  + str(config.generated_charts_path / config.file_name)
                  + " "
                  + str(DEFAULT_DENSITY))

        self.window.output_image_view.set_generated_image.emit(
            QPixmap(str(config.generated_charts_path / config.file_name) + ".png")
            , None
            , None)

    @pyqtSlot(object)
    def auto_straightening(self, chart) -> None:
        """
        pyqtSlot, which calls the function responsible for straighten the input image

        Args:
            chart: input image containing the chart to straighten

        Returns:
            None
        """
        try:
            straightened_chart = main_char_detections.start_char_detections(chart.copy(), None, None, True, None, None)
            height, width, _ = straightened_chart.shape
            bytes_per_line = 3 * width
            straightened_chart_pixmap = QPixmap.fromImage(
                QImage(straightened_chart.data, width, height, bytes_per_line, QImage.Format_BGR888))
            self.window.input_image_view.set_generated_image.emit(straightened_chart_pixmap, None, None)

        except Exception as e:
            logging.exception("An error occurred during auto straightening: %s", e)
            self.error_signal.emit([f"Hiba történt az automatikus kiegyenesítés során: {e}",
                                    "Próbálja meg manuálisan kiegyenesíteni a képet, hogy a program felismerhesse."])
            self.window.input_image_view.set_error_image_signal.emit()
            self.window.rotate_button.setHidden(True)
            self.window.legend_group.setHidden(True)
            self.window.title_group.setHidden(True)
            self.window.scanButton.setHidden(True)
