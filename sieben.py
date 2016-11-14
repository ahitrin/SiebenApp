#!/usr/bin/env python3.5
# coding: utf-8
import sys
from mikado import Goals
from subprocess import run
from system import dot_export
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QScrollArea
)


class SiebenApp(QMainWindow):
    refresh = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.scr = QScrollArea()
        self.l = QLabel()
        self.refresh.connect(self.reload_image)
        self.goals = Goals('Rename me')

    def setup(self):
        self.setWindowTitle('Sieben 7')
        self.resize(700, 500)
        self.scr.setWidget(self.l)
        self.setCentralWidget(self.scr)
        self.l.setScaledContents(True)
        self.l.setVisible(True)
        self.scr.setVisible(True)
        self.refresh.emit()

    def reload_image(self):
        with open('work.dot', 'w') as f:
            f.write(dot_export(self.goals))
        run(['dot', '-Tpng', '-o', 'work.png', 'work.dot'])
        img = QImage('work.png')
        self.l.setPixmap(QPixmap.fromImage(img))
        self.l.resize(img.size().width(), img.size().height())

    def keyPressEvent(self, event):
        # stupid handler for 'r'
        if event.key() == 82:
            self.refresh.emit()
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SiebenApp()
    w.setup()
    w.show()

    sys.exit(app.exec_())
