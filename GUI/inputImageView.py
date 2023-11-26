from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtGui import QPixmap, QPolygonF, QPainterPath, QPainter
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem
from GUI.viewWithScene import ViewWithScene


class InputImageView(ViewWithScene):
    cropped = pyqtSignal(QPixmap)

    # def __init__(self):
    #     super(InputImageView, self).__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pen_width = 5
        self.pen = QPen(Qt.green, self.pen_width)
        self.click_pos = []
        self.lines = []
        self.circles = []
        self.corner_diameter = 20

    def calculate_pen_width(self, width_scale, height_scale):
        self.pen_width = round(5 * max(width_scale, height_scale))
        # self.pen_width = 0.007 * min(self.pixmap_item.pixmap().width(), self.pixmap_item.pixmap().height())
        self.pen.setWidth(self.pen_width)

    def calculate_corner_diameter(self, width_scale, height_scale):
        # self.corner_diameter = 0.03 * min(self.pixmap_item.pixmap().width(), self.pixmap_item.pixmap().height())
        self.corner_diameter = round(15 * max(width_scale, height_scale))

    def calculate_scales(self):
        width_scale = self.pixmap_item.pixmap().width() / self.width()
        height_scale = self.pixmap_item.pixmap().height() / self.height()

        self.calculate_pen_width(width_scale, height_scale)
        self.calculate_corner_diameter(width_scale, height_scale)

    def mousePressEvent(self, event):
        event_pos = self.pixmap_item.mapFromScene(self.mapToScene(event.pos()))
        if event.button() == Qt.LeftButton and self.pixmap_item.contains(event_pos):

            self.click_pos.append(event_pos)
            self.draw_corner(event_pos)

            if 1 < len(self.click_pos) < 4:
                self.draw_line(self.click_pos[-2], event_pos)
                self.draw_corner(event_pos)

            elif len(self.click_pos) == 4:
                self.draw_line(self.click_pos[-2], event_pos)
                self.draw_line(self.click_pos[0], event_pos)
                self.draw_corner(event_pos)
                self.crop(self.click_pos)

            elif len(self.click_pos) == 5:
                for ln in self.lines:
                    self.scene().removeItem(ln)
                self.lines = []
                for c in self.circles[:-1]:
                    self.scene().removeItem(c)
                self.circles = [self.circles[-1]]
                self.click_pos = [event_pos]

        super().mousePressEvent(event)

    def draw_line(self, start_point, end_point):
        line = QGraphicsLineItem(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        line.setPen(self.pen)
        self.scene().addItem(line)
        self.lines.append(line)
        self.draw_corner(start_point)

    def draw_corner(self, click_pos):
        corner = QGraphicsEllipseItem(click_pos.x() - self.corner_diameter / 2,
                                      click_pos.y() - self.corner_diameter / 2,
                                      self.corner_diameter, self.corner_diameter)
        corner.setBrush(QBrush(Qt.red))
        self.scene().addItem(corner)
        self.circles.append(corner)

    def crop(self, click_pos):
        painter_path = QPainterPath()
        painter_path.addPolygon(QPolygonF(click_pos))
        source = self.pixmap_item.pixmap()
        r = painter_path.boundingRect().toRect().intersected(source.rect())

        pixmap = QPixmap(source.size())
        # print(source.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setClipPath(painter_path)
        painter.drawPixmap(QPoint(), source, source.rect())
        painter.end()
        result = pixmap.copy(r)
        self.cropped.emit(result)

    def clear_scene(self):
        if len(self.scene().items()) > 1:
            self.scene().clear()
            self.pixmap_item = self.scene().addPixmap(QPixmap())
            self.click_pos.clear()
            self.lines.clear()
            self.circles.clear()
