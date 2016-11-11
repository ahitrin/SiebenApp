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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = QMainWindow()
    w.setWindowTitle('Sieben 7')
    w.resize(500, 400)
    scr = QScrollArea()
    l = QLabel()
    scr.setWidget(l)
    w.setCentralWidget(scr)
    img = QImage('./doc/work.png')
    l.setPixmap(QPixmap.fromImage(img))
    l.resize(img.size().width(), img.size().height())
    l.setScaledContents(True)
    l.setVisible(True)
    scr.setVisible(True)
    w.show()

    sys.exit(app.exec_())
