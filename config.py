import logging
from pathlib import Path

from colorlog import ColoredFormatter


class Config:
    def __init__(self):
        self.file_name = ""
        self.resources_path = Path(__file__).resolve().parent / "resources"
        self.generated_charts_path = Path(__file__).resolve().parent / "generated_charts"
        self.convert_pdf_to_png_bat_file_path = self.resources_path / "convert_pdf_to_png.bat"
        self.ui_path = Path(__file__).resolve().parent / "ui"
        self.logger = self.setup_custom_logger()

    def setup_custom_logger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s -  "
            "%(log_color)s%(levelname)s -  "
            "%(log_color)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG': 'white',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
            },
            secondary_log_colors={}
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        return logger


config = Config()
