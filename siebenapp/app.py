#!/usr/bin/env python3.5
# coding: utf-8
import sys
from siebenapp.goaltree import Goals
from siebenapp.system import save, load, dot_export
from subprocess import run
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QLineEdit,
    QMainWindow,
    QScrollArea,
    QSizePolicy
)
from PyQt5.uic import loadUi


class SiebenApp(QMainWindow):
    refresh = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.refresh.connect(self.reload_image)
        self.quit_app.connect(QApplication.instance().quit)
        self.view  = 'open'
        self.goals = load()

    def setup(self):
        self.refresh.emit()

    def reload_image(self):
        save(self.goals)
        with open('work.dot', 'w') as f:
            f.write(dot_export(self.goals, self.view))
        run(['dot', '-Tpng', '-o', 'work.png', 'work.dot'])
        img = QImage('work.png')
        self.label.setPixmap(QPixmap.fromImage(img))
        self.label.resize(img.size().width(), img.size().height())

    def keyPressEvent(self, event):
        key_handlers = {
            Qt.Key_1: lambda: self.select_number(1),
            Qt.Key_2: lambda: self.select_number(2),
            Qt.Key_3: lambda: self.select_number(3),
            Qt.Key_4: lambda: self.select_number(4),
            Qt.Key_5: lambda: self.select_number(5),
            Qt.Key_6: lambda: self.select_number(6),
            Qt.Key_7: lambda: self.select_number(7),
            Qt.Key_8: lambda: self.select_number(8),
            Qt.Key_9: lambda: self.select_number(9),
            Qt.Key_0: lambda: self.select_number(0),
            Qt.Key_A: self.start_edit(self.goals.add),
            Qt.Key_C: self.with_refresh(self.goals.toggle_close),
            Qt.Key_D: self.with_refresh(self.goals.delete),
            Qt.Key_I: self.start_edit(self.goals.insert),
            Qt.Key_L: self.with_refresh(self.goals.toggle_link),
            Qt.Key_Q: self.quit_app.emit,
            Qt.Key_R: self.start_edit(self.goals.rename),
            Qt.Key_V: self.toggle_view,
            Qt.Key_Space: self.with_refresh(self.goals.hold_select),
        }
        if event.key() in key_handlers:
            key_handlers[event.key()]()
        else:
            super().keyPressEvent(event)

    def start_edit(self, fn):
        def inner():
            self.input.setEnabled(True)
            self.input.setFocus(True)
            self.input.returnPressed.connect(self.finish_edit(fn))
        return inner

    def finish_edit(self, fn):
        def inner():
            self.input.returnPressed.disconnect()
            fn(self.input.text())
            self.input.setEnabled(False)
            self.input.setText('')
            self.refresh.emit()
        return inner

    def with_refresh(self, fn):
        def inner():
            fn()
            self.refresh.emit()
        return inner

    def select_number(self, num):
        self.goals.select(num)
        self.refresh.emit()

    def toggle_view(self):
        next_view = {
            'full': 'open',
            'open': 'top',
            'top': 'full',
        }
        self.view = next_view[self.view]
        self.refresh.emit()


def main():
    app = QApplication(sys.argv)
    w = loadUi('siebenapp/main.ui', SiebenApp())
    w.setup()
    w.showMaximized()
    sys.exit(app.exec_())
