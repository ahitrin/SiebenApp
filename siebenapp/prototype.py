#!/usr/bin/env python3
# coding: utf-8
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget

from siebenapp.ui.goalwidget import Ui_GoalBody


class GoalWidget(QWidget, Ui_GoalBody):
    def __init__(self, name, number):
        super().__init__()
        self.setupUi(self)
        self.label_goal_name.setText(name)
        self.label_number.setText(number)


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QGridLayout())
        self.widgets = []
        self.lines = []

    def addCustomWidget(self, widget, row, column):
        self.layout().addWidget(widget, row, column)
        self.widgets.append(widget)

    def addCustomLine(self, upper, lower):
        self.lines.append((upper, lower))

    def paintEvent(self, paint_event):
        # pylint: disable=unused-argument
        painter = QPainter(self)
        painter.setRenderHint(painter.Antialiasing)
        painter.setPen(QColor(Qt.black))
        for upper, lower in self.lines:
            x1, y1 = self._lower_bound(upper)
            x2, y2 = self._upper_bound(lower)
            painter.drawLine(x1, y1, x2, y2)

    def _lower_bound(self, number):
        widget = self.widgets[number]
        x = widget.x() + (widget.width() / 2)
        y = widget.y() + widget.height() - 8
        return x, y

    def _upper_bound(self, number):
        widget = self.widgets[number]
        x = widget.x() + (widget.width() / 2)
        y = widget.y() + 8
        return x, y


def main():
    app = QApplication(sys.argv)
    w = QMainWindow()
    central_widget = CentralWidget()
    my_widgets = [
        (GoalWidget('one', '5'), 1, 1),
        (GoalWidget('two', '2'), 1, 2),
        (GoalWidget('An example of goal\nwith a long name', '3'), 2, 2),
        (GoalWidget('four', '1'), 2, 3),
        (GoalWidget('five', '4'), 3, 2),
    ]
    my_lines = [
        (0, 2), (1, 2),
        (2, 4), (3, 4),
    ]
    for widget, row, column in my_widgets:
        central_widget.addCustomWidget(widget, row, column)
    for upper, lower in my_lines:
        central_widget.addCustomLine(upper, lower)
    w.setCentralWidget(central_widget)
    w.show()
    sys.exit(app.exec_())
