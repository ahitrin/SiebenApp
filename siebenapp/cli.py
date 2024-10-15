import sys
import shutil
from argparse import ArgumentParser
from operator import itemgetter
from typing import Any
from collections.abc import Mapping

from siebenapp.autolink import ToggleAutoLink
from siebenapp.goaltree import OPTION_SELECT, OPTION_PREV_SELECT
from siebenapp.render import GoalsHolder
from siebenapp.domain import (
    ToggleClose,
    Delete,
    HoldSelect,
    ToggleLink,
    EdgeType,
    Select,
    Add,
    Insert,
    Rename,
    Graph,
    RenderResult,
    RenderRow,
    Command,
)
from siebenapp.progress_view import ToggleProgress
from siebenapp.filter_view import FilterBy
from siebenapp.open_view import ToggleOpenView
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import save, load
from siebenapp.zoom import ToggleZoom

USER_MESSAGE: str = ""


class IO:
    """Simple wrapper for all input/output interactions"""

    def write(self, text: str, *args) -> None:
        raise NotImplementedError

    def read(self) -> str:
        raise NotImplementedError

    def width(self) -> int:
        return 40


class ConsoleIO(IO):
    def __init__(self, prompt: str):
        super().__init__()
        sys.stdin.reconfigure(encoding="utf-8")  # type: ignore
        self.prompt = prompt

    def write(self, text: str, *args: str) -> None:
        print(text, *args)

    def read(self) -> str:
        return input(self.prompt)

    def width(self) -> int:
        return shutil.get_terminal_size((80, 20))[0]


def update_message(message: str = "") -> None:
    global USER_MESSAGE
    USER_MESSAGE = message


def fmt(render_result: RenderResult, row: RenderRow, id_width: int) -> str:
    def show_id() -> str:
        return " " * id_width if -10 <= int(row.goal_id) < 0 else str(row.goal_id)

    def status() -> str:
        op: str = " " if row.is_open else "x"
        return f"[{op}]" if row.is_switchable else f" {op} "

    def selection() -> str:
        if render_result.global_opts[OPTION_SELECT] == row.goal_id:
            return ">"
        elif render_result.global_opts[OPTION_PREV_SELECT] == row.goal_id:
            return "_"
        return " "

    def children() -> str:
        if not row.edges:
            return ""
        children: list[str] = []
        blockers: list[str] = []
        relates: list[str] = []
        for e in row.edges:
            if e[1] == EdgeType.PARENT:
                children.append(str(e[0]))
            elif e[1] == EdgeType.BLOCKER:
                blockers.append(str(e[0]))
            else:
                relates.append(str(e[0]))
        return f" [{','.join(children)} / {','.join(blockers)} | {','.join(relates)}]"

    def attributes() -> str:
        return (
            f" [{','.join(f'{k}: {row.attrs[k]}' for k in sorted(row.attrs))}]"
            if row.attrs
            else ""
        )

    return "".join(
        [show_id(), status(), selection(), row.name, children(), attributes()]
    )


def build_actions(command: str, goals_holder: GoalsHolder) -> list[Command]:
    target = int(goals_holder.goals.settings("selection"))
    simple_commands: Mapping[str, Command] = {
        "c": ToggleClose(),
        "d": Delete(),
        "h": HoldSelect(),
        "k": ToggleLink(edge_type=EdgeType.PARENT),
        "l": ToggleLink(),
        ";": ToggleLink(edge_type=EdgeType.RELATION),
        "n": ToggleOpenView(),
        "p": ToggleProgress(),
        "t": ToggleSwitchableView(),
        "z": ToggleZoom(target),
    }
    if command and all(c in "1234567890" for c in command):
        return [Select(int(c)) for c in command]
    if command.startswith("a "):
        return [Add(command.removeprefix("a "))]
    if command.startswith("i "):
        return [Insert(command.removeprefix("i "))]
    if command.startswith("r "):
        return [Rename(command.removeprefix("r "))]
    if command.startswith("f"):
        # Note: filter may be empty
        return [FilterBy(command.removeprefix("f").lstrip())]
    if command.startswith("`"):
        # Note: autolink may be empty
        return [ToggleAutoLink(command.removeprefix("`").lstrip(), target)]
    if command in simple_commands:
        return [simple_commands[command]]
    return []


def loop(io: IO, goals: Graph, db_name: str) -> None:
    cmd: str = ""
    goals_holder: GoalsHolder = GoalsHolder(goals, db_name)
    while cmd != "q":
        render_result, _ = goals_holder.render(100)
        index: list[tuple[RenderRow, Any, Any]] = sorted(
            [
                (
                    row,
                    render_result.node_opts[row.goal_id]["row"],
                    render_result.node_opts[row.goal_id]["col"],
                )
                for row in render_result.rows
            ],
            key=itemgetter(1, 2),
            reverse=True,
        )
        id_width: int = len(str(max(r.goal_id for r in render_result.rows)))
        io.write("-" * io.width())
        for row, _, __ in index:
            io.write(fmt(render_result, row, id_width))
        if USER_MESSAGE:
            io.write(USER_MESSAGE)
        update_message()
        try:
            cmd = io.read().strip()
        except EOFError:
            break
        actions = build_actions(cmd, goals_holder)
        goals_holder.accept(*actions)


def main() -> None:
    io = ConsoleIO(prompt="> ")
    parser = ArgumentParser()
    parser.add_argument(
        "db",
        nargs="?",
        default="sieben.db",
        help="Path to the database file",
    )
    args = parser.parse_args()
    goals = load(args.db, update_message)
    loop(io, goals, args.db)
