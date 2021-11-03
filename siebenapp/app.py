#!/usr/bin/env python3
# coding: utf-8
import sys
from argparse import ArgumentParser
from os.path import dirname, join, realpath

from PyQt5.QtCore import pyqtSignal, Qt, QRect, QPoint  # type: ignore
from PyQt5.QtGui import QPainter, QPen  # type: ignore
from PyQt5.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QWidget,
    QGridLayout,
    QFileDialog,
)
from PyQt5.uic import loadUi  # type: ignore

from siebenapp.domain import (
    EdgeType,
    HoldSelect,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Select,
    Insert,
    Rename,
)
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.open_view import ToggleOpenView
from siebenapp.render import Renderer
from siebenapp.system import save, load, split_long
from siebenapp.ui.goalwidget import Ui_GoalBody  # type: ignore
from siebenapp.zoom import ToggleZoom


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
        self.label_goal_name.setText(split_long(attributes["name"]))
        self.check_open.setVisible(attributes["switchable"])
        self.is_real = isinstance(number, int)
        if (selection := attributes["select"]) == "select":
            self.setStyleSheet("background-color:#808080;")
        elif selection == "prev":
            self.setStyleSheet("background-color:#C0C0C0;")
        if self.is_real:
            frame_color = "red" if attributes["open"] else "green"
            border = 2 if attributes["switchable"] else 1
            self.frame.setStyleSheet(
                f".QFrame{{ border: {border}px solid {frame_color} }}"
            )
            self.label_number.setText(str(number))
        else:
            self.setStyleSheet("color: #EEEEEE; border: #EEEEEE")

    def mousePressEvent(self, event):
        self._click_in_progress = True

    def mouseReleaseEvent(self, event):
        if self._click_in_progress:
            self.clicked.emit()
        self._click_in_progress = False


def top_left(w):
    return w.geometry().topLeft()


def top_right(w):
    return w.geometry().topRight()


def top_center(w):
    return (top_left(w) + top_right(w)) / 2


def bottom_left(w):
    return w.geometry().bottomLeft()


def bottom_right(w):
    return w.geometry().bottomRight()


def bottom_center(w):
    return (bottom_left(w) + bottom_right(w)) / 2


class CentralWidget(QWidget):
    EDGE_PENS = {
        EdgeType.BLOCKER: QPen(Qt.black, 1, Qt.DashLine),  # type: ignore
        EdgeType.PARENT: QPen(Qt.black, 1, Qt.SolidLine),  # type: ignore
    }

    def __init__(self):
        super().__init__()
        self.setGeometry(QRect(0, 0, 576, 273))
        self.setObjectName("scrollAreaWidgetContents")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.render_result = None

    def setupData(self, render_result):
        self.render_result = render_result

    def itemAt(self, row, col):
        return self.layout().itemAtPosition(row, col)

    def paintEvent(self, event):
        painter = QPainter(self)
        edges = {}
        lines = {EdgeType.BLOCKER: [], EdgeType.PARENT: []}

        for goal_id, attrs in self.render_result.graph.items():
            for e_target, e_type in attrs["edge"]:
                target_attrs = self.render_result.graph[e_target]
                if isinstance(goal_id, int):
                    start = top_center(self.itemAt(attrs["row"], attrs["col1"]))
                else:
                    left_id, p, q = self.render_result.edge_opts[goal_id]
                    if left_id > 0:
                        left = self.render_result.graph[left_id]["col1"]
                        left_widget = self.itemAt(attrs["row"], left)
                        right_widget = self.itemAt(attrs["row"], left + 1)
                        x1 = top_right(left_widget)
                        if right_widget is not None:
                            x2 = top_left(right_widget)
                        else:
                            x2 = x1 + QPoint(10 * q, 0)
                        start = x1 + (x2 - x1) / q * p
                    else:
                        right_widget = self.itemAt(attrs["row"], 0)
                        x2 = top_left(right_widget)
                        x1 = QPoint(0, x2.y())
                        start = x1 + (x2 - x1) / q * p
                    if goal_id not in edges:
                        edges[goal_id] = {"bottom": start, "style": e_type}
                    else:
                        edges[goal_id]["bottom"] = start
                        edges[goal_id]["style"] = max(edges[goal_id]["style"], e_type)
                if isinstance(e_target, int):
                    end = bottom_center(
                        self.itemAt(target_attrs["row"], target_attrs["col1"])
                    )
                else:
                    left_id, p, q = self.render_result.edge_opts[e_target]
                    if left_id > 0:
                        left = self.render_result.graph[left_id]["col1"]
                        left_widget = self.itemAt(target_attrs["row"], left)
                        right_widget = self.itemAt(target_attrs["row"], left + 1)
                        x1 = bottom_right(left_widget)
                        if right_widget is not None:
                            x2 = bottom_left(right_widget)
                        else:
                            x2 = x1 + QPoint(10 * q, 0)
                        end = x1 + (x2 - x1) / q * p
                    else:
                        right_widget = self.itemAt(target_attrs["row"], 0)
                        x2 = bottom_left(right_widget)
                        x1 = QPoint(0, x2.y())
                        end = x1 + (x2 - x1) / q * p
                    if e_target not in edges:
                        edges[e_target] = {"top": end, "style": e_type}
                    else:
                        edges[e_target]["top"] = end
                        edges[e_target]["style"] = max(edges[e_target]["style"], e_type)
                lines[e_type].append((start, end))

        for edge_type in lines:
            painter.setPen(self.EDGE_PENS[edge_type])
            for start, end in lines[edge_type]:
                painter.drawLine(start, end)
        for e in edges.values():
            painter.setPen(self.EDGE_PENS[e["style"]])
            painter.drawLine(e["bottom"], e["top"])


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
        self.action_New.triggered.connect(self.show_new_dialog)
        self.action_Open.triggered.connect(self.show_open_dialog)
        self.action_Hotkeys.triggered.connect(self.hotkeys.show)
        self.action_About.triggered.connect(self.about.show)
        self.toggleOpen.clicked.connect(self.with_refresh(self.toggle_open_view, False))
        self.toggleSwitchable.clicked.connect(
            self.with_refresh(self.toggle_switchable_view, False)
        )
        # Re-creation of scrollAreaWidgetContents looks like dirty hack,
        # but at the current moment I haven't found a better solution.
        # Widget creation in __init__ does not work: lines disappear.
        self.scrollAreaWidgetContents = CentralWidget()
        # End of 'looks like dirty hack'
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self._update_title()
        self.refresh.emit()

    def _update_title(self):
        self.setWindowTitle(f"{self.db} - SiebenApp")

    def close_goal(self, goal_id):
        def inner():
            self.goals.accept_all(Select(goal_id), ToggleClose())
            self.refresh.emit()

        return inner

    def save_and_render(self):
        if not self.goals.events() and not self.force_refresh:
            return
        self.force_refresh = False
        self.statusBar().clearMessage()
        save(self.goals, self.db)
        for child in self.scrollAreaWidgetContents.children():
            if isinstance(child, GoalWidget):
                child.deleteLater()
        render_result = Renderer(self.goals).build()
        if "setupData" in dir(self.scrollAreaWidgetContents):
            self.scrollAreaWidgetContents.setupData(render_result)
        for goal_id, attributes in render_result.graph.items():
            if isinstance(goal_id, int):
                widget = GoalWidget()
                self.scrollAreaWidgetContents.layout().addWidget(
                    widget, attributes["row"], attributes["col1"]
                )
                widget.setup_data(goal_id, attributes)
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
            Qt.Key_A: self.start_edit("Add new goal", self.emit_add),
            Qt.Key_C: self.with_refresh(self.goals.accept, ToggleClose()),
            Qt.Key_D: self.with_refresh(self.goals.accept, Delete()),
            Qt.Key_I: self.start_edit("Insert new goal", self.emit_insert),
            Qt.Key_K: self.with_refresh(
                self.goals.accept, ToggleLink(edge_type=EdgeType.PARENT)
            ),
            Qt.Key_L: self.with_refresh(self.goals.accept, ToggleLink()),
            Qt.Key_N: self.with_refresh(self.toggle_open_view, True),
            Qt.Key_O: self.show_open_dialog,
            Qt.Key_Q: self.quit_app.emit,
            Qt.Key_R: self.start_edit(
                "Rename goal", self.emit_rename, self._current_goal_label
            ),
            Qt.Key_T: self.with_refresh(self.toggle_switchable_view, True),
            Qt.Key_Z: self.toggle_zoom,
            Qt.Key_Escape: self.cancel_edit,
            Qt.Key_Space: self.with_refresh(self.goals.accept, HoldSelect()),
            Qt.Key_Slash: self.show_keys_help,
        }
        if event.key() in key_handlers:
            key_handlers[event.key()]()
        else:
            super().keyPressEvent(event)

    def show_new_dialog(self):
        name = QFileDialog.getSaveFileName(self, caption="Save as...", filter="*.db")[0]
        if name:
            if not name.endswith(".db"):
                name = name + ".db"
            self.db = name
            self.goals = load(name, self.show_user_message)
            self._update_title()
            self.force_refresh = True
            self.refresh.emit()

    def show_open_dialog(self):
        name = QFileDialog.getOpenFileName(self, caption="Open file", filter="*.db")[0]
        if name:
            self.db = name
            self.goals = load(name, self.show_user_message)
            self._update_title()
            self.force_refresh = True
            self.refresh.emit()

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
            self.dockWidget.setWindowTitle("")
            self.input.returnPressed.disconnect()
            fn(self.input.text())
            self.input.setEnabled(False)
            self.input.setText("")
            self.cancel.setEnabled(False)
            self.cancel.clicked.disconnect()
            self.refresh.emit()

        return inner

    def cancel_edit(self):
        self.dockWidget.setWindowTitle("")
        self.input.setEnabled(False)
        self.input.setText("")
        self.cancel.setEnabled(False)
        try:
            self.input.returnPressed.disconnect()
            self.cancel.clicked.disconnect()
        except TypeError:
            pass

    def emit_add(self, text):
        self.goals.accept(Add(text))

    def emit_insert(self, text):
        self.goals.accept(Insert(text))

    def emit_rename(self, text):
        self.goals.accept(Rename(text))

    def _current_goal_label(self):
        data = self.goals.q(keys="name,select").values()
        return [x["name"] for x in data if x["select"] == "select"].pop()

    def with_refresh(self, fn, *args, **kwargs):
        def inner():
            fn(*args, **kwargs)
            self.refresh.emit()

        return inner

    def select_number(self, num):
        def inner():
            self.goals.accept(Select(num))
            self.refresh.emit()

        return inner

    def toggle_open_view(self, update_ui):
        self.force_refresh = True
        self.goals.accept(ToggleOpenView())
        if update_ui:
            self.toggleOpen.setChecked(self.goals.settings("filter_open"))
        self._update_title()

    def toggle_switchable_view(self, update_ui):
        self.force_refresh = True
        self.goals.accept(ToggleSwitchableView())
        if update_ui:
            self.toggleSwitchable.setChecked(self.goals.settings("filter_switchable"))
        self._update_title()

    def toggle_zoom(self):
        self.force_refresh = True
        self.goals.accept(ToggleZoom())
        self.refresh.emit()

    def show_keys_help(self):
        self.action_Hotkeys.trigger()

    def show_user_message(self, message):
        self.statusBar().showMessage(message, 10000)


def main(root_script):
    parser = ArgumentParser()
    parser.add_argument(
        "db",
        nargs="?",
        default="sieben.db",
        help="Path to the database file (default: sieben.db)",
    )
    args = parser.parse_args()
    app = QApplication(sys.argv)
    root = dirname(realpath(root_script))
    w = loadUi(join(root, "ui", "main.ui"), SiebenApp(args.db))
    w.about = loadUi(join(root, "ui", "about.ui"))
    w.hotkeys = loadUi(join(root, "ui", "hotkeys.ui"))
    w.setup()
    w.showMaximized()
    sys.exit(app.exec_())
