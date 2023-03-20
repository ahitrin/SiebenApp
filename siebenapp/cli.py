import sys
from argparse import ArgumentParser
from operator import itemgetter
from typing import List, Mapping, Tuple, Any

from siebenapp.autolink import ToggleAutoLink
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


class ConsoleIO(IO):
    def __init__(self, prompt: str):
        super().__init__()
        sys.stdin.reconfigure(encoding="utf-8")  # type: ignore
        self.prompt = prompt

    def write(self, text: str, *args: str) -> None:
        print(text, *args)

    def read(self) -> str:
        return input(self.prompt)


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
        if render_result.select[0] == row.goal_id:
            return ">"
        elif render_result.select[1] == row.goal_id:
            return "_"
        return " "

    def children() -> str:
        if not row.edges:
            return ""
        child_list: str = ",".join(
            str(e[0]) for e in row.edges if e[1] == EdgeType.PARENT
        )
        blocker_list: str = ",".join(
            str(e[0]) for e in row.edges if e[1] == EdgeType.BLOCKER
        )
        return f" [{child_list} / {blocker_list}]"

    def attributes() -> str:
        return (
            f" [{','.join(f'{k}: {row.attrs[k]}' for k in sorted(row.attrs))}]"
            if row.attrs
            else ""
        )

    return "".join(
        [show_id(), status(), selection(), row.name, children(), attributes()]
    )


def build_actions(command: str) -> List[Command]:
    simple_commands: Mapping[str, Command] = {
        "c": ToggleClose(),
        "d": Delete(),
        "h": HoldSelect(),
        "k": ToggleLink(edge_type=EdgeType.PARENT),
        "l": ToggleLink(),
        "n": ToggleOpenView(),
        "p": ToggleProgress(),
        "t": ToggleSwitchableView(),
        "z": ToggleZoom(),
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
        return [ToggleAutoLink(command.removeprefix("`").lstrip())]
    if command in simple_commands:
        return [simple_commands[command]]
    return []


def loop(io: IO, goals: Graph, db_name: str) -> None:
    cmd: str = ""
    goals_holder: GoalsHolder = GoalsHolder(goals, db_name)
    while cmd != "q":
        render_result, _ = goals_holder.render(100)
        index: List[Tuple[RenderRow, Any, Any]] = sorted(
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
        for row, _, __ in index:
            io.write(fmt(render_result, row, id_width))
        if USER_MESSAGE:
            io.write(USER_MESSAGE)
        update_message()
        try:
            cmd = io.read().strip()
        except EOFError:
            break
        actions = build_actions(cmd)
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
