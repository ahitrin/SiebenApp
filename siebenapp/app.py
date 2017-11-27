#!/usr/bin/env python3
# coding: utf-8
import sys
from argparse import ArgumentParser
from os.path import dirname, join, realpath
from subprocess import run

from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
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
        self.use_dot = True
        self.force_refresh = True

    def setup(self):
        self.action_About.triggered.connect(self.about.show)
        self.refresh.emit()

    def reload_image(self):
        if not self.goals.events and not self.force_refresh:
            return
        self.force_refresh = False
        save(self.goals, self.db)
        if self.use_dot:
            with open('work.dot', 'w') as f:
                f.write(dot_export(self.goals))
            run(['dot', '-Tpng', '-o', 'work.png', 'work.dot'])
            img = QImage('work.png')
            self.label.setPixmap(QPixmap.fromImage(img))
            self.label.resize(img.size().width(), img.size().height())

    def keyPressEvent(self, event):
        key_handlers = {
            Qt.Key_1: self.select_number(1),
            Qt.Key_2: self.select_number(2),
            Qt.Key_3: self.select_number(3),
            Qt.Key_4: self.select_number(4),
            Qt.Key_5: self.select_number(5),
            Qt.Key_6: self.select_number(6),
            Qt.Key_7: self.select_number(7),
            Qt.Key_8: self.select_number(8),
            Qt.Key_9: self.select_number(9),
            Qt.Key_0: self.select_number(0),
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
        def inner():
            self.goals.select(num)
            self.refresh.emit()
        return inner

    def toggle_view(self):
        self.force_refresh = True
        self.goals.next_view()
        self.refresh.emit()

    def toggle_zoom(self):
        self.force_refresh = True
        self.goals.toggle_zoom()
        self.refresh.emit()


class GoalWidget(QWidget, Ui_GoalBody):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._click_in_progress = False
        self.setupUi(self)

    def setup_data(self, number, attributes):
        self.label_goal_name.setText(split_long(attributes['name']))
        self.label_number.setText(str(number))
        self.check_open.setVisible(attributes['switchable'])
        selection = attributes['select']
        if selection == 'select':
            self.setStyleSheet('background-color:#808080;')
        elif selection == 'prev':
            self.setStyleSheet('background-color:#C0C0C0;')
        frame_color = 'red' if attributes['open'] else 'green'
        self.frame.setStyleSheet('.QFrame{ border: 1px solid %s }' % frame_color)

    def mousePressEvent(self, event):                           # pylint: disable=unused-argument
        self._click_in_progress = True

    def mouseReleaseEvent(self, event):                         # pylint: disable=unused-argument
        if self._click_in_progress:
            self.clicked.emit()
        self._click_in_progress = False

    def get_id(self):
        return int(self.label_number.text())


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(QRect(0, 0, 576, 273))
        self.setObjectName('scrollAreaWidgetContents')
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.dependencies = dict()

    def setDependencies(self, new_dependencies):
        self.dependencies = new_dependencies

    @staticmethod
    def top_point(rect):
        return (rect.topLeft() + rect.topRight()) / 2

    @staticmethod
    def bottom_point(rect):
        return (rect.bottomLeft() + rect.bottomRight()) / 2

    def paintEvent(self, event):                                    # pylint: disable=unused-argument
        painter = QPainter(self)
        painter.setPen(Qt.black)

        widgets = {w.get_id(): (self.top_point(w.geometry()), self.bottom_point(w.geometry()))
                   for w in self.children() if isinstance(w, GoalWidget)}
        for widget_id, points in widgets.items():
            line_start = points[0]
            for parent_widget in self.dependencies[widget_id]:
                line_end = widgets[parent_widget][1]
                painter.drawLine(line_start, line_end)


class SiebenAppDevelopment(SiebenApp):
    def __init__(self, db):
        super(SiebenAppDevelopment, self).__init__(db)
        self.refresh.connect(self.native_render)

    def setup(self):
        super().setup()
        # Re-creation of scrollAreaWidgetContents looks like dirty hack,
        # but at the current moment I haven't found a better solution.
        # Widget creation in __init__ does not work: lines disappear.
        # Also we have to disable pylint warning in order to make build green.
        self.scrollAreaWidgetContents = CentralWidget()         # pylint: disable=attribute-defined-outside-init
        # End of 'looks like dirty hack'
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.refresh.emit()

    def close_goal(self, goal_id):
        def inner():
            self.goals.select(goal_id)
            self.goals.toggle_close()
            self.refresh.emit()
        return inner

    def native_render(self):
        for child in self.scrollAreaWidgetContents.children():
            if isinstance(child, GoalWidget):
                child.deleteLater()
        graph = render_tree(self.goals)
        if 'setDependencies' in dir(self.scrollAreaWidgetContents):
            self.scrollAreaWidgetContents.setDependencies({g: graph[g]['edge'] for g in graph})
        for goal_id, attributes in graph.items():
            widget = GoalWidget()
            self.scrollAreaWidgetContents.layout().addWidget(widget, attributes['row'], attributes['col'])
            widget.setup_data(goal_id, attributes)
            widget.clicked.connect(self.select_number(goal_id))
            widget.check_open.clicked.connect(self.close_goal(goal_id))
        self.scrollAreaWidgetContents.update()


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
    w.use_dot = not args.devel
    w.about = loadUi(join(root, 'ui', 'about.ui'))
    w.setup()
    w.showMaximized()
    sys.exit(app.exec_())
