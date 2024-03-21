import cv2
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QRubberBand

from viewWithScene import ViewWithScene


class InputImageViewMouseDrag(ViewWithScene):
    cropped = pyqtSignal(np.ndarray)

    # def __init__(self):
    #     super(InputImageView, self).__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crop_rect = QRect
        self.img = None
        self.originQPoint = None
        self.currentQRubberBand = None
        self.enable_crop = False
        self.setDragMode(ViewWithScene.RubberBandDrag)
        self.cropped_pos = None
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
            self.cropped_pos = current_q_rect
            self.crop_rect = QRect(self.mapToScene(current_q_rect.topLeft()).toPoint(),
                                   self.mapToScene(current_q_rect.bottomRight()).toPoint()).normalized()
            # self.currentQRubberBand.deleteLater()
            crop_q_pixmap = self.pixmap_item.pixmap().copy(self.crop_rect)
            self.crop_image(crop_q_pixmap)

    def crop_image(self, qimg):
        qimage = qimg.toImage()
        width, height = qimage.width(), qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = bytearray(ptr)

        img = cv2.cvtColor(
            np.array(arr).reshape(height, width, 4),
            cv2.COLOR_RGBA2BGR
        )
        self.cropped.emit(img)

    def clear_scene(self):
        if len(self.scene.items()) > 1:
            self.scene.clear()
            self.pixmap_item = self.scene.addPixmap(QPixmap())

    def set_image(self, pixmap):
        w = pixmap.width()
        h = pixmap.height()
        self.aspect_ratio = round(w / h, 4)
        if h > w:
            print(" h > w")
            h = self.optimal_size
            w = int(h * self.aspect_ratio)
            self.resize_ratio = round(pixmap.height() / h, 4)
        else:
            w = self.optimal_size
            h = int(w / self.aspect_ratio)
            self.resize_ratio = round(pixmap.width() / w, 4)

        print(f"\tInputImageView resized from {pixmap.width()}x{pixmap.height()} to {w}x{h}, aspect_ratio: {self.aspect_ratio}, resize_ratio {self.resize_ratio}")
        self.setFixedSize(w, h)
        self.image = pixmap
        self.pixmap_item.setPixmap(pixmap)
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
