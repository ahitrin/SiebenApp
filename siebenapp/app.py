#!/usr/bin/env python3
# coding: utf-8
import sys
from argparse import ArgumentParser
from os.path import dirname, join, realpath

from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PyQt5.uic import loadUi

from siebenapp.goaltree import Edge
from siebenapp.render import Renderer
from siebenapp.system import save, load, DEFAULT_DB, split_long
from siebenapp.ui.goalwidget import Ui_GoalBody


class GoalWidget(QWidget, Ui_GoalBody):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._click_in_progress = False
        self.setupUi(self)
        self.is_real = True
        self.widget_id = None

    def setup_data(self, number, attributes):
        self.widget_id = number
        self.label_goal_name.setText(split_long(attributes['name']))
        self.check_open.setVisible(attributes['switchable'])
        self.is_real = isinstance(number, int)
        selection = attributes['select']
        if selection == 'select':
            self.setStyleSheet('background-color:#808080;')
        elif selection == 'prev':
            self.setStyleSheet('background-color:#C0C0C0;')
        if self.is_real:
            frame_color = 'red' if attributes['open'] else 'green'
            border = 2 if attributes['switchable'] else 1
            self.frame.setStyleSheet('.QFrame{ border: %dpx solid %s }' % (border, frame_color))
            self.label_number.setText(str(number))
        else:
            self.setStyleSheet('color: #EEEEEE; border: #EEEEEE')

    def mousePressEvent(self, event):                           # pylint: disable=unused-argument
        self._click_in_progress = True

    def mouseReleaseEvent(self, event):                         # pylint: disable=unused-argument
        if self._click_in_progress:
            self.clicked.emit()
        self._click_in_progress = False

    def top_point(self):
        rect = self.geometry()
        return (rect.topLeft() + rect.topRight()) / 2

    def bottom_point(self):
        rect = self.geometry()
        return (rect.bottomLeft() + rect.bottomRight()) / 2


class CentralWidget(QWidget):
    EDGE_PENS = {
        Edge.BLOCKER: QPen(Qt.black, 1, Qt.DashLine),
        Edge.PARENT: QPen(Qt.black, 1, Qt.SolidLine),
    }

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

    def paintEvent(self, event):                                    # pylint: disable=unused-argument
        painter = QPainter(self)

        widgets = {w.widget_id: (w.top_point(), w.bottom_point(), w.is_real)
                   for w in self.children() if isinstance(w, GoalWidget)}
        for widget_id, points in widgets.items():
            line_start = points[0]
            for edge in self.dependencies[widget_id]:
                line_end = widgets[edge[0]][1]
                painter.setPen(self.EDGE_PENS[edge[1]])
                painter.drawLine(line_start, line_end)
            if not points[2]:
                style = max([e[1] for e in self.dependencies[widget_id]])
                painter.setPen(self.EDGE_PENS[style])
                painter.drawLine(points[0], points[1])


class SiebenApp(QMainWindow):
    refresh = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh.connect(self.save_and_render)
        self.quit_app.connect(QApplication.instance().quit)
        self.db = db
        self.goals = load(db, self.show_user_message)
        self.force_refresh = True

    def setup(self):
        self.action_Hotkeys.triggered.connect(self.hotkeys.show)
        self.action_About.triggered.connect(self.about.show)
        # Re-creation of scrollAreaWidgetContents looks like dirty hack,
        # but at the current moment I haven't found a better solution.
        # Widget creation in __init__ does not work: lines disappear.
        # Also we have to disable pylint warning in order to make build green.
        self.scrollAreaWidgetContents = CentralWidget()         # pylint: disable=attribute-defined-outside-init
        # End of 'looks like dirty hack'
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self._update_title()
        self.refresh.emit()

    def _update_title(self):
        self.setWindowTitle('{0} ({1} view) - SiebenApp'.format(self.db, self.goals.view))

    def close_goal(self, goal_id):
        def inner():
            self.goals.select(goal_id)
            self.goals.toggle_close()
            self.refresh.emit()
        return inner

    def save_and_render(self):
        if not self.goals.events and not self.force_refresh:
            return
        self.force_refresh = False
        self.statusBar().clearMessage()
        save(self.goals, self.db)
        for child in self.scrollAreaWidgetContents.children():
            if isinstance(child, GoalWidget):
                child.deleteLater()
        graph = Renderer(self.goals).build()
        if 'setDependencies' in dir(self.scrollAreaWidgetContents):
            self.scrollAreaWidgetContents.setDependencies({g: graph[g]['edge'] for g in graph})
        for goal_id, attributes in graph.items():
            widget = GoalWidget()
            self.scrollAreaWidgetContents.layout().addWidget(widget, attributes['row'], attributes['col'])
            widget.setup_data(goal_id, attributes)
            if isinstance(goal_id, int):
                widget.clicked.connect(self.select_number(goal_id))
                widget.check_open.clicked.connect(self.close_goal(goal_id))
        self.scrollAreaWidgetContents.update()

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
            Qt.Key_A: self.start_edit('Add new goal', self.goals.add),
            Qt.Key_C: self.with_refresh(self.goals.toggle_close),
            Qt.Key_D: self.with_refresh(self.goals.delete),
            Qt.Key_I: self.start_edit('Insert new goal', self.goals.insert),
            Qt.Key_K: self.with_refresh(self.goals.toggle_link, edge_type=Edge.PARENT),
            Qt.Key_L: self.with_refresh(self.goals.toggle_link),
            Qt.Key_Q: self.quit_app.emit,
            Qt.Key_R: self.start_edit('Rename goal', self.goals.rename, self._current_goal_label),
            Qt.Key_V: self.toggle_view,
            Qt.Key_Z: self.toggle_zoom,
            Qt.Key_Escape: self.cancel_edit,
            Qt.Key_Space: self.with_refresh(self.goals.hold_select),
            Qt.Key_Slash: self.show_keys_help,
        }
        if event.key() in key_handlers:
            key_handlers[event.key()]()
        else:
            super().keyPressEvent(event)

    def start_edit(self, label, fn, pre_fn=None):
        def inner():
            self.dockWidget.setWindowTitle(label)
            self.input.setEnabled(True)
            self.input.setFocus(True)
            if pre_fn is not None:
                self.input.setText(pre_fn())
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

    def _current_goal_label(self):
        data = self.goals.q(keys='name,select').values()
        return [x['name'] for x in data if x['select'] == 'select'].pop()

    def with_refresh(self, fn, *args, **kwargs):
        def inner():
            fn(*args, **kwargs)
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
        self._update_title()
        self.refresh.emit()

    def toggle_zoom(self):
        self.force_refresh = True
        self.goals.toggle_zoom()
        self.refresh.emit()

    def show_keys_help(self):
        self.action_Hotkeys.trigger()

    def show_user_message(self, message):
        self.statusBar().showMessage(message, 10000)


def main(root_script):
    parser = ArgumentParser()
    parser.add_argument('db', nargs='?', default=DEFAULT_DB,
                        help='Path to the database file (sieben.db by default)')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    root = dirname(realpath(root_script))
    w = loadUi(join(root, 'ui', 'main.ui'), SiebenApp(args.db))
    w.about = loadUi(join(root, 'ui', 'about.ui'))
    w.hotkeys = loadUi(join(root, 'ui', 'hotkeys.ui'))
    w.setup()
    w.showMaximized()
    sys.exit(app.exec_())
