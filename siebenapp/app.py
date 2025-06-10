#!/usr/bin/env python3
import sys
from argparse import ArgumentParser
from os.path import dirname, join, realpath
from typing import Any

from PySide6.QtCore import Signal, Qt, QRect, QFile, QIODevice, QEvent  # type: ignore
from PySide6.QtGui import QPainter, QPen  # type: ignore
from PySide6.QtUiTools import QUiLoader  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QWidget,
    QGridLayout,
    QFileDialog,
)

from siebenapp.autolink import ToggleAutoLink
from siebenapp.selectable import OPTION_SELECT, OPTION_PREV_SELECT, Select, HoldSelect
from siebenapp.progress_view import ToggleProgress
from siebenapp.filter_view import FilterBy
from siebenapp.domain import (
    EdgeType,
    ToggleClose,
    Delete,
    ToggleLink,
    Add,
    Insert,
    Rename,
    RenderRow,
    RenderResult,
    GoalId,
)
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.open_view import ToggleOpenView
from siebenapp.render import Renderer, GeometryProvider, render_lines, GoalsHolder
from siebenapp.system import load, split_long
from siebenapp.ui.goalwidget import Ui_GoalBody  # type: ignore
from siebenapp.zoom import ToggleZoom


class GoalWidget(QWidget, Ui_GoalBody):
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self._click_in_progress = False
        self.setupUi(self)
        self.widget_id = None

    def setup_data(self, row: RenderRow, selection: tuple[GoalId, GoalId]) -> None:
        self.widget_id = row.goal_id
        self.label_goal_name.setText(split_long(row.name))
        self.check_open.setVisible(row.is_switchable)
        if selection[0] == row.goal_id:
            self.setStyleSheet("background-color:#808080;")
        elif selection[1] == row.goal_id:
            self.setStyleSheet("background-color:#C0C0C0;")
        frame_color = "red" if row.is_open else "green"
        border = 2 if row.is_switchable else 1
        self.frame.setStyleSheet(f".QFrame{{ border: {border}px solid {frame_color} }}")
        if isinstance(row.goal_id, int) and row.goal_id >= 0:
            self.label_number.setText(str(row.goal_id))
        if row.attrs:
            row_text = "\n".join(f"{k}: {split_long(row.attrs[k])}" for k in row.attrs)
            self.label_attrs.setText(row_text)
            self.label_attrs.setVisible(True)
        else:
            self.label_attrs.setVisible(False)

    def mousePressEvent(self, event):
        self._click_in_progress = True

    def mouseReleaseEvent(self, event):
        if self._click_in_progress:
            self.clicked.emit()
        self._click_in_progress = False


class CentralWidget(QWidget):
    __metaclass__ = GeometryProvider

    EDGE_PENS = {
        EdgeType.RELATION: QPen(Qt.black, 1, Qt.DotLine),  # type: ignore
        EdgeType.BLOCKER: QPen(Qt.black, 1.2, Qt.DashLine),  # type: ignore
        EdgeType.PARENT: QPen(Qt.black, 1.3, Qt.SolidLine),  # type: ignore
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
        if col < 0:
            g = self.itemAt(row, 0).geometry()
            return QRect(0, g.topLeft().y(), 0, g.height())
        item = self.layout().itemAtPosition(row, col)
        if item is not None:
            return item
        g = self.itemAt(row, col - 1).geometry()
        return QRect(g.topRight().x() + 100, g.topRight().y(), 0, g.height())

    def top_left(self, row, col):
        w = self.itemAt(row, col)
        return w.topLeft() if isinstance(w, QRect) else w.geometry().topLeft()

    def top_right(self, row, col):
        w = self.itemAt(row, col)
        return w.topRight() if isinstance(w, QRect) else w.geometry().topRight()

    def bottom_left(self, row, col):
        w = self.itemAt(row, col)
        return w.bottomLeft() if isinstance(w, QRect) else w.geometry().bottomLeft()

    def bottom_right(self, row, col):
        w = self.itemAt(row, col)
        return w.bottomRight() if isinstance(w, QRect) else w.geometry().bottomRight()

    def paintEvent(self, event):
        painter = QPainter(self)
        lines = render_lines(self, self.render_result)

        for edge_type, start, end, _ in lines:
            painter.setPen(self.EDGE_PENS[edge_type])
            painter.drawLine(start, end)


class SiebenApp(QMainWindow):
    refresh = Signal()
    quit_app = Signal()

    def __init__(self, db, experimental, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh.connect(self.save_and_render)
        self.quit_app.connect(QApplication.instance().quit)
        goals = load(db, self.show_user_message)
        self.classic_render = not experimental
        self.goals_holder = GoalsHolder(goals, db, self.classic_render)
        self.columns = Renderer.DEFAULT_WIDTH

    def setup(self):
        self.centralWidget().action_New.triggered.connect(self.show_new_dialog)
        self.centralWidget().action_Open.triggered.connect(self.show_open_dialog)
        self.centralWidget().action_Hotkeys.triggered.connect(self.hotkeys.show)
        self.centralWidget().action_About.triggered.connect(self.about.show)
        self.centralWidget().actionQuit.triggered.connect(self.quit_app)
        self.centralWidget().toggleOpen.clicked.connect(
            self.with_refresh(self.toggle_open_view, False)
        )
        self.centralWidget().toggleSwitchable.clicked.connect(
            self.with_refresh(self.toggle_switchable_view, False)
        )
        self.centralWidget().toggleProgress.clicked.connect(
            self.with_refresh(self.toggle_progress_view, False)
        )
        # Re-creation of scrollAreaWidgetContents looks like dirty hack,
        # but at the current moment I haven't found a better solution.
        # Widget creation in __init__ does not work: lines disappear.
        self.centralWidget().scrollAreaWidgetContents = CentralWidget()
        # End of 'looks like dirty hack'
        self.centralWidget().scrollArea.setWidget(
            self.centralWidget().scrollAreaWidgetContents
        )
        self.centralWidget().installEventFilter(self)
        self._reset_controls_and_title()
        self.refresh.emit()

    def _reset_controls_and_title(self):
        """Set application title and revert controls to defaults."""
        self.centralWidget().setWindowTitle(f"{self.goals_holder.filename} - SiebenApp")
        self.centralWidget().toggleOpen.setChecked(True)
        self.centralWidget().toggleSwitchable.setChecked(False)
        self.centralWidget().toggleProgress.setChecked(False)

    def close_goal(self, goal_id):
        def inner():
            self.goals_holder.accept(ToggleClose(goal_id))
            self.refresh.emit()

        return inner

    def save_and_render(self):
        render_result, partial_change = self.goals_holder.render(self.columns)
        if "setupData" in dir(self.centralWidget().scrollAreaWidgetContents):
            self.centralWidget().scrollAreaWidgetContents.setupData(render_result)
        if not partial_change:
            for child in self.centralWidget().scrollAreaWidgetContents.children():
                if isinstance(child, GoalWidget):
                    child.deleteLater()
            for row in render_result.rows:
                self._make_widget(render_result, row)
        else:
            for child in self.centralWidget().scrollAreaWidgetContents.children():
                if isinstance(child, GoalWidget) and child.widget_id in partial_change:
                    child.deleteLater()
            for row_id in partial_change:
                row = render_result.by_id(row_id)
                self._make_widget(render_result, row)
        self.centralWidget().scrollAreaWidgetContents.update()

    def _make_widget(self, render_result: RenderResult, row: RenderRow) -> None:
        attributes = render_result.node_opts[row.goal_id]
        widget = GoalWidget()
        self.centralWidget().scrollAreaWidgetContents.layout().addWidget(  # type: ignore
            widget, attributes["row"], attributes["col"]
        )
        widget.setup_data(
            row,
            (
                render_result.global_opts[OPTION_SELECT],
                render_result.global_opts[OPTION_PREV_SELECT],
            ),
        )
        widget.clicked.connect(self.select_number(row.goal_id))
        widget.check_open.clicked.connect(self.close_goal(row.raw_id))

    def settings(self, name: str) -> Any:
        return self.goals_holder.goals.settings(name)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            self.keyPressEvent(event)
            return False
        return super().eventFilter(obj, event)

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
            Qt.Key_C: self.with_refresh(self.goals_holder.accept, ToggleClose()),
            Qt.Key_D: self.start_edit('Type "yes" to delete a goal', self.emit_delete),
            Qt.Key_F: self.start_edit(
                "Filter by substring (leave empty to reset filtration)",
                self.emit_filter,
            ),
            Qt.Key_I: self.start_edit("Insert new goal", self.emit_insert),
            Qt.Key_K: self.with_refresh(
                self.goals_holder.accept, ToggleLink(edge_type=EdgeType.PARENT)
            ),
            Qt.Key_L: self.with_refresh(self.goals_holder.accept, ToggleLink()),
            Qt.Key_N: self.with_refresh(self.toggle_open_view, True),
            Qt.Key_O: self.show_open_dialog,
            Qt.Key_P: self.with_refresh(self.toggle_progress_view, True),
            Qt.Key_Q: self.quit_app.emit,
            Qt.Key_R: self.start_edit(
                "Rename goal", self.emit_rename, self._current_goal_label
            ),
            Qt.Key_T: self.with_refresh(self.toggle_switchable_view, True),
            Qt.Key_Z: self.toggle_zoom,
            Qt.Key_QuoteLeft: self.start_edit(
                "Auto link by keyword (leave empty to reset auto link)",
                self.emit_autolink,
            ),
            Qt.Key_Escape: self.cancel_edit,
            Qt.Key_Minus: self.with_refresh(self.change_columns, -1),
            Qt.Key_Plus: self.with_refresh(self.change_columns, 1),
            Qt.Key_Slash: self.show_keys_help,
            Qt.Key_Semicolon: self.with_refresh(
                self.goals_holder.accept, ToggleLink(edge_type=EdgeType.RELATION)
            ),
            Qt.Key_Space: self.with_refresh(self.goals_holder.accept, HoldSelect()),
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
            goals = load(name, self.show_user_message)
            self.goals_holder = GoalsHolder(goals, name, self.classic_render)
            self._reset_controls_and_title()
            self.refresh.emit()

    def show_open_dialog(self):
        name = QFileDialog.getOpenFileName(self, caption="Open file", filter="*.db")[0]
        if name:
            goals = load(name, self.show_user_message)
            self.goals_holder = GoalsHolder(goals, name, self.classic_render)
            self._reset_controls_and_title()
            self.refresh.emit()

    def start_edit(self, label, fn, pre_fn=None):
        def inner():
            self.centralWidget().dockWidget.setWindowTitle(label)
            self.centralWidget().input.setEnabled(True)
            self.centralWidget().input.setFocus()
            if pre_fn is not None:
                self.centralWidget().input.setText(pre_fn())
            self.centralWidget().input.returnPressed.connect(self.finish_edit(fn))
            self.centralWidget().cancel.setEnabled(True)
            self.centralWidget().cancel.clicked.connect(self.cancel_edit)

        return inner

    def finish_edit(self, fn):
        def inner():
            self.centralWidget().dockWidget.setWindowTitle("")
            self.centralWidget().input.returnPressed.disconnect()
            fn(self.centralWidget().input.text())
            self.centralWidget().input.setEnabled(False)
            self.centralWidget().input.setText("")
            self.centralWidget().cancel.setEnabled(False)
            self.centralWidget().cancel.clicked.disconnect()
            self.refresh.emit()

        return inner

    def cancel_edit(self):
        self.centralWidget().dockWidget.setWindowTitle("")
        self.centralWidget().input.setEnabled(False)
        self.centralWidget().input.setText("")
        self.centralWidget().cancel.setEnabled(False)
        try:
            self.centralWidget().input.returnPressed.disconnect()
            self.centralWidget().cancel.clicked.disconnect()
        except TypeError:
            pass

    def emit_add(self, text):
        self.goals_holder.accept(Add(text))

    def emit_insert(self, text):
        self.goals_holder.accept(Insert(text))

    def emit_rename(self, text):
        self.goals_holder.accept(Rename(text))

    def emit_filter(self, text):
        self.goals_holder.accept(FilterBy(text))

    def emit_autolink(self, text):
        target = int(self.settings("selection"))
        self.goals_holder.accept(ToggleAutoLink(text, target))

    def emit_delete(self, text):
        if text == "yes":
            target = int(self.settings("selection"))
            self.goals_holder.accept(Delete(target))

    def _current_goal_label(self):
        render_result = self.goals_holder.goals.q()
        current_row = render_result.by_id(render_result.global_opts[OPTION_SELECT])
        return current_row.name

    def with_refresh(self, fn, *args, **kwargs):
        def inner():
            fn(*args, **kwargs)
            self.refresh.emit()

        return inner

    def select_number(self, num):
        def inner():
            self.goals_holder.accept(Select(num))
            self.refresh.emit()

        return inner

    def toggle_open_view(self, update_ui):
        self.goals_holder.accept(ToggleOpenView())
        if update_ui:
            self.centralWidget().toggleOpen.setChecked(self.settings("filter_open"))

    def toggle_switchable_view(self, update_ui):
        self.goals_holder.accept(ToggleSwitchableView())
        if update_ui:
            self.centralWidget().toggleSwitchable.setChecked(
                self.settings("filter_switchable")
            )

    def toggle_progress_view(self, update_ui):
        self.goals_holder.accept(ToggleProgress())
        if update_ui:
            self.centralWidget().toggleProgress.setChecked(
                self.settings("filter_progress")
            )

    def toggle_zoom(self):
        target = int(self.settings("selection"))
        self.goals_holder.accept(ToggleZoom(target))
        self.refresh.emit()

    def show_keys_help(self):
        self.centralWidget().action_Hotkeys.trigger()

    def show_user_message(self, message):
        self.centralWidget().statusBar().showMessage(message, 10000)

    def change_columns(self, delta):
        new_columns = self.columns + delta
        if 1 <= new_columns <= 100:
            self.columns = new_columns


def loadUi(file_path: str, parent) -> QWidget:
    loader = QUiLoader()
    qfile = QFile(file_path)
    qfile.open(QIODevice.ReadOnly)  # type: ignore
    widget = loader.load(qfile, parent)
    qfile.close()
    return widget


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "db",
        nargs="?",
        default="sieben.db",
        help="Path to the database file (default: sieben.db)",
    )
    parser.add_argument(
        "-x",
        "--experimental",
        action="store_true",
        default=False,
        help="Enable experimental features",
    )
    args = parser.parse_args()
    app = QApplication(sys.argv)
    root = dirname(realpath(__file__))
    sieben = SiebenApp(args.db, args.experimental)
    w = loadUi(join(root, "ui", "main.ui"), sieben)
    sieben.about = loadUi(join(root, "ui", "about.ui"), sieben)
    sieben.hotkeys = loadUi(join(root, "ui", "hotkeys.ui"), sieben)
    sieben.setup()
    w.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # For debugging
    main()
