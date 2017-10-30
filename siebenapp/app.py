#!/usr/bin/env python3
# coding: utf-8
import sys
from argparse import ArgumentParser
from os.path import dirname, join, realpath
from subprocess import run

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.uic import loadUi

from siebenapp.render import render_tree
from siebenapp.system import save, load, dot_export, DEFAULT_DB, split_long
from siebenapp.ui.goalwidget import Ui_GoalBody


class SiebenApp(QMainWindow):
    refresh = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.refresh.connect(self.reload_image)
        self.quit_app.connect(QApplication.instance().quit)
        self.db = db
        self.goals = load(db)
        self.force_refresh = True

    def setup(self):
        self.action_About.triggered.connect(self.about.show)
        self.refresh.emit()

    def reload_image(self):
        if not self.goals.events and not self.force_refresh:
            return
        self.force_refresh = False
        save(self.goals, self.db)
        with open('work.dot', 'w') as f:
            f.write(dot_export(self.goals))
        if 'label' in self.__dict__:
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
            Qt.Key_A: self.start_edit(self.goals.add, 'Add new goal'),
            Qt.Key_C: self.with_refresh(self.goals.toggle_close),
            Qt.Key_D: self.with_refresh(self.goals.delete),
            Qt.Key_I: self.start_edit(self.goals.insert, 'Insert new goal'),
            Qt.Key_L: self.with_refresh(self.goals.toggle_link),
            Qt.Key_Q: self.quit_app.emit,
            Qt.Key_R: self.start_edit(self.goals.rename, 'Rename goal'),
            Qt.Key_S: self.with_refresh(self.goals.swap_goals),
            Qt.Key_V: self.toggle_view,
            Qt.Key_Z: self.toggle_zoom,
            Qt.Key_Escape: self.cancel_edit,
            Qt.Key_Space: self.with_refresh(self.goals.hold_select),
        }
        if event.key() in key_handlers:
            key_handlers[event.key()]()
        else:
            super().keyPressEvent(event)

    def start_edit(self, fn, dock_label):
        def inner():
            self.dockWidget.setWindowTitle(dock_label)
            self.input.setEnabled(True)
            self.input.setFocus(True)
            self.input.returnPressed.connect(self.finish_edit(fn))
            self.cancel.setEnabled(True)
            self.cancel.clicked.connect(self.cancel_edit)
        return inner

    def finish_edit(self, fn):
        def inner():
            self.dockWidget.setWindowTitle('')
            self.input.returnPressed.disconnect()
            fn(self.input.text())
            self.input.setEnabled(False)
            self.input.setText('')
            self.cancel.setEnabled(False)
            self.cancel.clicked.disconnect()
            self.refresh.emit()
        return inner

    def cancel_edit(self):
        self.dockWidget.setWindowTitle('')
        self.input.setEnabled(False)
        self.input.setText('')
        self.cancel.setEnabled(False)
        try:
            self.input.returnPressed.disconnect()
            self.cancel.clicked.disconnect()
        except TypeError:
            pass

    def with_refresh(self, fn):
        def inner():
            fn()
            self.refresh.emit()
        return inner

    def select_number(self, num):
        self.goals.select(num)
        self.refresh.emit()

    def toggle_view(self):
        self.force_refresh = True
        self.goals.next_view()
        self.refresh.emit()

    def toggle_zoom(self):
        self.force_refresh = True
        self.goals.toggle_zoom()
        self.refresh.emit()


class GoalWidget(QWidget, Ui_GoalBody):
    def __init__(self, name, number, selection):
        super().__init__()
        self.setupUi(self)
        self.label_goal_name.setText(name)
        self.label_number.setText(str(number))
        if selection == 'select':
            self.setStyleSheet('background-color:#808080;')
        elif selection == 'prev':
            self.setStyleSheet('background-color:#C0C0C0;')


class SiebenAppDevelopment(SiebenApp):
    def __init__(self, db):
        super(SiebenAppDevelopment, self).__init__(db)
        self.refresh.connect(self.native_render)

    def native_render(self):
        graph = render_tree(self.goals)
        for goal_id, attributes in graph.items():
            widget = GoalWidget(split_long(attributes['name']), goal_id, attributes['select'])
            self.centralWidget().layout().addWidget(widget, attributes['row'], attributes['col'])


def main(root_script):
    parser = ArgumentParser()
    parser.add_argument('--devel', '-d', action='store_true', default=False,
                        help='Run in developer mode (affects GUI behavior)')
    parser.add_argument('db', nargs='?', default=DEFAULT_DB,
                        help='Path to the database file (sieben.db by default)')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    root = dirname(realpath(root_script))
    if args.devel:
        w = loadUi(join(root, 'ui', 'main-devel.ui'), SiebenAppDevelopment(args.db))
    else:
        w = loadUi(join(root, 'ui', 'main.ui'), SiebenApp(args.db))
    w.about = loadUi(join(root, 'ui', 'about.ui'))
    w.setup()
    w.showMaximized()
    sys.exit(app.exec_())
