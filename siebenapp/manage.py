from argparse import ArgumentParser
from html import escape
from os import path
from siebenapp.cli import IO, ConsoleIO
from siebenapp.domain import EdgeType
from siebenapp.open_view import ToggleOpenView
from siebenapp.progress_view import ToggleProgress
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import load, save, extract_subtree, split_long
from typing import List, Optional, Dict


def print_dot(args, io: IO):
    tree = load(args.db)
    if args.n:
        tree.accept(ToggleOpenView())
    if args.p:
        tree.accept(ToggleProgress())
    if args.t:
        tree.accept(ToggleSwitchableView())
    io.write(dot_export(tree))


def migrate(args, io: IO):
    goals = load(args.db)
    save(goals, args.db)


def extract(args, io: IO):
    tree = load(args.source_db).goaltree.goaltree
    assert not path.exists(args.target_db), f"File {args.target_db} already exists!"
    result = extract_subtree(tree, args.goal_id)
    save(result, args.target_db)


def _flag(parser, key, description) -> None:
    parser.add_argument(key, required=False, action="store_true", help=description)


def main(argv: Optional[List[str]] = None, io: Optional[IO] = None):
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title="commands")

    parser_dot = subparsers.add_parser("dot")
    _flag(parser_dot, "-n", "Show closed goals (same as n key in the app)")
    _flag(parser_dot, "-p", "Show goal progress (same as p key in the app)")
    _flag(parser_dot, "-t", "Show only switchable goals (same as t key in app)")
    parser_dot.add_argument("db")
    parser_dot.set_defaults(func=print_dot)

    parser_migrate = subparsers.add_parser("migrate")
    parser_migrate.add_argument("db")
    parser_migrate.set_defaults(func=migrate)

    parser_extract = subparsers.add_parser("extract")
    parser_extract.add_argument(
        "source_db",
        help="An existing file with goaltree to extract. "
        "This file will not be modified during the operation. You may/should do it manually.",
    )
    parser_extract.add_argument(
        "target_db",
        help="A new file to be created. It will contain a result of extraction. "
        "Only subgoals and edges are extracted, no zoom and/or autolink data is inherited.",
    )
    parser_extract.add_argument(
        "goal_id",
        type=int,
        help="An id of the goal that should be set as a root goal of a new goaltree. "
        "All of its subgoals will be copied too (but not blockers). "
        "The simplest way to find a real id of a goal is to run `sieben-manage dot` on the source file.",
    )
    parser_extract.set_defaults(func=extract)

    args = parser.parse_args(argv)
    io = io or ConsoleIO("> ")
    if "func" in dir(args):
        args.func(args, io)
    else:
        parser.print_help()


def _format_name(num: int, goal: Dict[str, str]) -> str:
    goal_name = escape(goal["name"])
    label = f'"{num}: {goal_name}"' if num >= 0 else f'"{goal_name}"'
    return split_long(label)


def dot_export(goals):
    data = goals.q(keys="open,name,edge,switchable")
    lines = []
    for num in sorted(data.keys()):
        goal = data[num]
        attributes = {
            "label": _format_name(num, goal),
            "color": "red" if goal["open"] else "green",
        }
        if goal["switchable"] and goal["open"]:
            attributes["style"] = "bold"
        attributes_str = ", ".join(
            f"{k}={attributes[k]}"
            for k in ["label", "color", "style", "fillcolor"]
            if k in attributes and attributes[k]
        )
        lines.append(f"{num} [{attributes_str}];")
    for num in sorted(data.keys()):
        for edge in data[num]["edge"]:
            color = "black" if data[edge[0]]["open"] else "gray"
            line_attrs = f"color={color}"
            if edge[1] == EdgeType.BLOCKER:
                line_attrs += ", style=dashed"
            lines.append(f"{edge[0]} -> {num} [{line_attrs}];")
    body = "\n".join(lines)
    return f"digraph g {{\nnode [shape=box];\n{body}\n}}"
