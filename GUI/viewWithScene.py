import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene


class ViewWithScene(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(ViewWithScene, self).__init__(QGraphicsScene(), *args, **kwargs)
        # super(ViewWithScene, self).__init__(QGraphicsScene())
        self.resize_ratio = 0
        self.aspect_ratio = 0
        self.pixmap_item = self.scene().addPixmap(QPixmap())
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.optimal_size = 700
        self.image = None
        self.original_size = None

    def set_image(self, img):
        pixmap = img
        if type(img) == np.ndarray:
            height, width, _ = img.shape
            bytesPerLine = 3 * width
            pixmap = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(pixmap)

        w = pixmap.width()
        h = pixmap.height()
        # self.original_size = (w, h)
        self.aspect_ratio = round(w / h, 4)
        if h > w:
            print(" h > w")
            h = self.optimal_size
            w = int(h * self.aspect_ratio)
            self.resize_ratio = round(pixmap.height() / h, 4)
            # print(f"{self.resize_ratio} {h / self.optimal_size}")
        else:
            w = self.optimal_size
            h = int(w / self.aspect_ratio)
            self.resize_ratio = round(pixmap.width() / w, 4)

        # print(f"{round(self.resize_ratio, 4)}")
        # print(f"{min(round(w / self.optimal_size, 4), round(self.optimal_size / w, 4))}")
        # print(f"{round(self.optimal_size / h, 4)}")
        # print(f"{round(pixmap.height() / h, 4)}")
        # print(f"{round(pixmap.width() / w, 4)}")

        # print(f"{pixmap.width() / w}, {pixmap.height() / h}")
        print(f"View resized from {pixmap.width()}x{pixmap.height()} to {w}x{h}, aspect_ratio: {self.aspect_ratio}, resize_ratio {self.resize_ratio}")
        self.setFixedSize(w, h)
        self.image = pixmap
        self.pixmap_item.setPixmap(pixmap)
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
