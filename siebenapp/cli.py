import sys
from argparse import ArgumentParser
from operator import itemgetter

from siebenapp.autolink import ToggleAutoLink
from siebenapp.render import Renderer
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
)
from siebenapp.progress_view import ToggleProgress
from siebenapp.filter_view import FilterBy
from siebenapp.open_view import ToggleOpenView
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import save, load
from siebenapp.zoom import ToggleZoom

USER_MESSAGE = ""


class IO:
    """Simple wrapper for all input/output interactions"""

    def write(self, text: str, *args) -> None:
        raise NotImplementedError

    def read(self) -> str:
        raise NotImplementedError


class ConsoleIO(IO):
    def __init__(self, prompt):
        super().__init__()
        sys.stdin.reconfigure(encoding="utf-8")
        self.prompt = prompt

    def write(self, text: str, *args) -> None:
        print(text, *args)

    def read(self) -> str:
        return input(self.prompt)


def update_message(message=""):
    global USER_MESSAGE
    USER_MESSAGE = message


def fmt(render_result: RenderResult, row: RenderRow, id_width):
    show_id = " " * id_width if -10 <= int(row.goal_id) < 0 else row.goal_id
    op = " " if row.is_open else "x"
    status = f"[{op}]" if row.is_switchable else f" {op} "
    selection = " "
    if render_result.select[0] == row.goal_id:
        selection = ">"
    elif render_result.select[1] == row.goal_id:
        selection = "_"
    children = ""
    if row.edges:
        child_list = ",".join(str(e[0]) for e in row.edges if e[1] == EdgeType.PARENT)
        blocker_list = ",".join(
            str(e[0]) for e in row.edges if e[1] == EdgeType.BLOCKER
        )
        children = f" [{child_list} / {blocker_list}]"
    attributes = (
        f" [{','.join(f'{k}: {row.attrs[k]}' for k in sorted(row.attrs))}]"
        if row.attrs
        else ""
    )
    return f"{show_id}{status}{selection}{row.name}{children}{attributes}"


def build_actions(command):
    simple_commands = {
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
        return [Add(command[2:])]
    if command.startswith("i "):
        return [Insert(command[2:])]
    if command.startswith("r "):
        return [Rename(command[2:])]
    if command.startswith("f"):
        return [FilterBy(command[1:].lstrip())]
    if command.startswith("` "):
        return [ToggleAutoLink(command[2:])]
    if command in simple_commands:
        return [simple_commands[command]]
    return []


def loop(io: IO, goals: Graph, db_name: str):
    cmd = ""
    while cmd != "q":
        render_result = Renderer(goals, 100).build()
        rows = render_result.rows
        index = sorted(
            [
                (
                    row,
                    render_result.graph[row.goal_id]["row"],
                    render_result.graph[row.goal_id]["col"],
                )
                for row in rows
            ],
            key=itemgetter(1, 2),
            reverse=True,
        )
        id_width = len(str(max(r.goal_id for r in rows)))
        for item in index:
            row = item[0]
            io.write(fmt(render_result, row, id_width))
        if USER_MESSAGE:
            io.write(USER_MESSAGE)
        update_message()
        try:
            cmd = io.read().strip()
        except EOFError:
            break
        actions = build_actions(cmd)
        if actions:
            goals.accept_all(*actions)
        save(goals, db_name)


def main():
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
