import sys
from argparse import ArgumentParser

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
)
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


def fmt(goal_id, goal_vars):
    name = goal_vars["name"]
    op = " " if goal_vars["open"] else "x"
    status = f"[{op}]" if goal_vars["switchable"] else f" {op} "
    selection = " "
    if goal_vars["select"] == "select":
        selection = ">"
    elif goal_vars["select"] == "prev":
        selection = "_"
    children = ""
    if goal_vars["edge"]:
        child_list = ",".join(str(e[0]) for e in goal_vars["edge"])
        children = f" [{child_list}]"
    return f"{goal_id}{status}{selection}{name}{children}"


def build_actions(command):
    simple_commands = {
        "c": ToggleClose(),
        "d": Delete(),
        "h": HoldSelect(),
        "k": ToggleLink(edge_type=EdgeType.PARENT),
        "l": ToggleLink(),
        "n": ToggleOpenView(),
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
    if command in simple_commands:
        return [simple_commands[command]]
    return []


def loop(io: IO, goals: Graph, db_name: str):
    cmd = ""
    while cmd != "q":
        x = goals.q("name,edge,open,select,switchable")
        for goal_id, goal_vars in x.items():
            io.write(fmt(goal_id, goal_vars))
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
