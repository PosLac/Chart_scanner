from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene


class ViewWithScene(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(ViewWithScene, self).__init__(QGraphicsScene(), *args, **kwargs)
        # super(ViewWithScene, self).__init__(QGraphicsScene())
        self.pixmap_item = self.scene().addPixmap(QPixmap())
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumSize(800, 800)
        self.image = None

    def set_image(self, pixmap):
        self.image = pixmap
        self.pixmap_item.setPixmap(pixmap)
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
