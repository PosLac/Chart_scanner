import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QLabel

from config import config

logger = config.logger


class QGraphicsViewWithScene(QGraphicsView):
    set_generated_image = pyqtSignal(QPixmap, object, object)
    start_spinner_signal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QGraphicsViewWithScene, self).__init__(*args, **kwargs)
        self.scene = QGraphicsScene()
        self.resize_ratio = 1
        self.aspect_ratio = 1
        self.pixmap_item = self.scene.addPixmap(QPixmap())
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.optimal_size = 700
        self.image = None
        self.set_generated_image.connect(self.set_image)
        self.movie = QMovie(str(config.resources_path / "Spin-1s-200px.gif"))
        self.label = None
        self.item = None
        logger.info(f"{self.__class__.__name__} inited")

    def add_label(self):
        self.scene.clear()
        self.label = QLabel()
        self.item = self.scene.addWidget(self.label)
        self.label.setMovie(self.movie)
        self.label.setGeometry(0, 0, 200, 200)
        self.movie.start()
        self.item.setPos((self.scene.width() - self.label.width()) / 2,
                         (self.scene.height() - self.label.height()) / 2)

    def set_error_image(self):
        self.scene.clear()
        self.setFixedSize(200, 200)
        self.pixmap_item = self.scene.addPixmap(QPixmap())
        self.image = QPixmap(str(config.resources_path / "corrupted_image_icon.png"))
        self.pixmap_item.setPixmap(self.image)
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def set_image(self, pixmap, width=None, height=None):
        if width == 0 or height == 0:
            self.set_error_image()
        try:
            if width is None or height is None:
                width = pixmap.width()
                height = pixmap.height()

                self.aspect_ratio = round(width / height, 4)
                if height > width:
                    height = self.optimal_size
                    width = int(height * self.aspect_ratio)
                    self.resize_ratio = round(pixmap.height() / height, 4)
                else:
                    width = self.optimal_size
                    height = int(width / self.aspect_ratio)
                    self.resize_ratio = round(pixmap.width() / width, 4)

                logging.info(f"{self.__class__.__name__} resized from ({pixmap.width()} x {pixmap.height()}) "
                             f"to ({width} x {height}), aspect_ratio: {self.aspect_ratio}, resize_ratio {self.resize_ratio}")
            self.scene.clear()
            self.setFixedSize(width, height)
            self.pixmap_item = self.scene.addPixmap(QPixmap())
            self.image = pixmap
            self.pixmap_item.setPixmap(pixmap)
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

        except Exception as e:
            self.set_error_image()
            logger.error("There was an error during image setting to view, setting error image: %s", e)

