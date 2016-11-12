#!/usr/bin/env python3.5
# coding: utf-8
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QScrollArea
)
from PyQt5.QtGui import QImage, QPixmap


class SiebenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scr = QScrollArea()
        self.l = QLabel()
        self.img = QImage('./doc/work.png')

    def setup(self):
        self.setWindowTitle('Sieben 7')
        self.resize(700, 500)
        self.scr.setWidget(self.l)
        self.setCentralWidget(self.scr)
        self.l.setPixmap(QPixmap.fromImage(self.img))
        self.l.resize(self.img.size().width(), self.img.size().height())
        self.l.setScaledContents(True)
        self.l.setVisible(True)
        self.scr.setVisible(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SiebenApp()
    w.setup()
    w.show()

    sys.exit(app.exec_())
