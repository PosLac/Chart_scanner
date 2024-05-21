from PyQt5.QtCore import pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QRubberBand

from config import config
from .qGraphicsViewWithScene import QGraphicsViewWithScene

logger = config.logger


class InputImageQGraphicsView(QGraphicsViewWithScene):
    """
    QGraphicsViewWithScene for input images
    """
    cropped = pyqtSignal(QPixmap)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crop_rect = None
        self.img = None
        self.originQPoint = None
        self.currentQRubberBand = None
        self.enable_crop = False
        self.setDragMode(QGraphicsViewWithScene.RubberBandDrag)
        self.file_name = ""

    def mousePressEvent(self, event):
        if self.enable_crop:
            self.originQPoint = event.pos()
            self.currentQRubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.currentQRubberBand.setGeometry(QRect(self.originQPoint, QSize()))
            self.currentQRubberBand.show()

    def mouseMoveEvent(self, event):
        if self.currentQRubberBand:
            self.currentQRubberBand.setGeometry(QRect(self.originQPoint, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if self.currentQRubberBand:
            self.currentQRubberBand.hide()
            current_q_rect = self.currentQRubberBand.geometry()
            self.crop_rect = QRect(self.mapToScene(current_q_rect.topLeft()).toPoint(),
                                   self.mapToScene(current_q_rect.bottomRight()).toPoint()).normalized()
            crop_q_pixmap = self.pixmap_item.pixmap().copy(self.crop_rect)
            self.cropped.emit(crop_q_pixmap)

    def clear_scene(self):
        if len(self.scene.items()) > 1:
            self.scene.clear()
            self.pixmap_item = self.scene.addPixmap(QPixmap())
