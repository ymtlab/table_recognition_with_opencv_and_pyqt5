# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QStyle
import sys

class RangeSlider(QtWidgets.QWidget):

    slider_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.first_position = 1
        self.second_position = 8

        self.style_option_slider = QtWidgets.QStyleOptionSlider()
        self.style_option_slider.minimum = 0
        self.style_option_slider.maximum = 10

        #self.setTickPosition(QtWidgets.QSlider.TicksAbove)
        #self.setTickInterval(1)

        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding, 
                QtWidgets.QSizePolicy.Fixed, 
                QtWidgets.QSizePolicy.Slider
            )
        )

    def setMinimum(self, minimum):
        self.style_option_slider.minimum = minimum

    def setMaximum(self, maximum):
        self.style_option_slider.maximum = maximum

    def setOrientation(self, value):
        self.orientation = value

    def setObjectName(self, value):
        self.objectName = value

    def setRangeLimit(self, minimum: int, maximum: int):
        self.style_option_slider.minimum = minimum
        self.style_option_slider.maximum = maximum

    def setRange(self, start: int, end: int):
        self.first_position = start
        self.second_position = end

    def getRange(self):
        return (self.first_position, self.second_position)

    #def setTickPosition(self, position: QtWidgets.QSlider.TickPosition):
        #self.style_option_slider.tickPosition = position

    #def setTickInterval(self, ti: int):
        #self.style_option_slider.tickInterval = ti

    def paintEvent(self, event: QtGui.QPaintEvent):

        painter = QtGui.QPainter(self)

        # Draw rule
        self.style_option_slider.initFrom(self)
        self.style_option_slider.rect = self.rect()
        self.style_option_slider.sliderPosition = 0
        self.style_option_slider.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderTickmarks

        #   Draw GROOVE
        self.style().drawComplexControl(QStyle.CC_Slider, self.style_option_slider, painter)

        #  Draw INTERVAL
        color = self.palette().color(QtGui.QPalette.Highlight)
        color.setAlpha(160)
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)

        self.style_option_slider.sliderPosition = self.first_position
        x_left_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.style_option_slider, QStyle.SC_SliderHandle)
            .right()
        )

        self.style_option_slider.sliderPosition = self.second_position
        x_right_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.style_option_slider, QStyle.SC_SliderHandle)
            .left()
        )

        groove_rect = self.style().subControlRect(
            QStyle.CC_Slider, self.style_option_slider, QStyle.SC_SliderGroove
        )

        selection = QtCore.QRect(
            x_left_handle,
            groove_rect.y(),
            x_right_handle - x_left_handle,
            groove_rect.height(),
        ).adjusted(-1, 1, 1, -1)

        painter.drawRect(selection)

        # Draw first handle
        self.style_option_slider.subControls = QStyle.SC_SliderHandle
        self.style_option_slider.sliderPosition = self.first_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.style_option_slider, painter)

        # Draw second handle
        self.style_option_slider.sliderPosition = self.second_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.style_option_slider, painter)

    def mousePressEvent(self, event: QtGui.QMouseEvent):

        self.style_option_slider.sliderPosition = self.first_position
        self._first_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.style_option_slider, event.pos(), self
        )

        self.style_option_slider.sliderPosition = self.second_position
        self._second_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.style_option_slider, event.pos(), self
        )

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):

        distance = self.style_option_slider.maximum - self.style_option_slider.minimum

        pos = self.style().sliderValueFromPosition(
            0, distance, event.pos().x(), self.rect().width()
        )

        if self._first_sc == QStyle.SC_SliderHandle:
            if pos <= self.second_position:
                self.first_position = pos
                self.update()
                self.slider_changed.emit()
                return

        if self._second_sc == QStyle.SC_SliderHandle:
            if pos >= self.first_position:
                self.second_position = pos
                self.update()
                self.slider_changed.emit()

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5

        w = SliderLength
        h = self.style().pixelMetric(QStyle.PM_SliderThickness, self.style_option_slider, self)

        if (
            self.style_option_slider.tickPosition & QtWidgets.QSlider.TicksAbove
            or self.style_option_slider.tickPosition & QtWidgets.QSlider.TicksBelow
        ):
            h += TickSpace

        return (
            self.style()
            .sizeFromContents(QStyle.CT_Slider, self.style_option_slider, QtCore.QSize(w, h), self)
            .expandedTo(QtWidgets.QApplication.globalStrut())
        )

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    range_slider = RangeSlider()

    range_slider.setRangeLimit(0, 100)
    range_slider.setRange(1, 99)

    range_slider.show()

    # q = QtWidgets.QSlider()
    # q.show()

    app.exec_()
