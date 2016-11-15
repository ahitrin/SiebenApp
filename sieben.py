#!/usr/bin/env python3.5
# coding: utf-8
import sys
from mikado import Goals
from os import path
from subprocess import run
from system import save, load, dot_export
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


class SiebenApp(QMainWindow):
    refresh = pyqtSignal()
    add_goal = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.scr = QScrollArea()
        self.l = QLabel()
        self.dock = QDockWidget('Edit area')
        self.input = QLineEdit()
        self.refresh.connect(self.reload_image)
        self.add_goal.connect(self.start_adding_goal)
        self.quit_app.connect(QApplication.instance().quit)
        if path.exists('sieben.db'):
            self.goals = load()
        else:
            self.goals = Goals('Rename me')

    def setup(self):
        self.setWindowTitle('Sieben 7')
        self.resize(700, 500)
        self.scr.setWidget(self.l)
        self.setCentralWidget(self.scr)
        self.l.setScaledContents(True)
        self.dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.dock.setWidget(self.input)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock)
        self.l.setVisible(True)
        self.scr.setVisible(True)
        self.dock.setVisible(True)
        self.input.setVisible(True)
        self.input.setEnabled(False)
        self.refresh.emit()

    def reload_image(self):
        save(self.goals)
        with open('work.dot', 'w') as f:
            f.write(dot_export(self.goals))
        run(['dot', '-Tpng', '-o', 'work.png', 'work.dot'])
        img = QImage('work.png')
        self.l.setPixmap(QPixmap.fromImage(img))
        self.l.resize(img.size().width(), img.size().height())

    def keyPressEvent(self, event):
        key_handlers = {
            Qt.Key_A: lambda: self.add_goal.emit(),
            Qt.Key_Q: lambda: self.quit_app.emit(),
            Qt.Key_R: lambda: self.refresh.emit(),
        }
        if event.key() in key_handlers:
            key_handlers[event.key()]()
        else:
            super().keyPressEvent(event)

    def start_adding_goal(self):
        self.input.setEnabled(True)
        self.input.setFocus(True)
        self.input.editingFinished.connect(self.end_adding_goal)

    def end_adding_goal(self):
        self.input.editingFinished.disconnect()
        goal_name = self.input.text()
        self.goals.add(goal_name)
        self.input.setEnabled(False)
        self.input.setText('')
        self.refresh.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SiebenApp()
    w.setup()
    w.show()

    sys.exit(app.exec_())
