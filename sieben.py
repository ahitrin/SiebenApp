#!/usr/bin/env python3.5
# coding: utf-8
import sys
from PyQt5.QtWidgets import QApplication, QWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = QWidget()
    w.resize(250, 150)
    w.setWindowTitle('Sieben 7')
    w.show()

    sys.exit(app.exec_())
