from argparse import ArgumentParser
from html import escape
from os import path
from siebenapp.cli import IO, ConsoleIO
from siebenapp.domain import EdgeType, Graph
from siebenapp.goaltree import Goals, GoalsData, EdgesData, OptionsData
from siebenapp.layers import get_root, persistent_layers
from siebenapp.open_view import ToggleOpenView
from siebenapp.progress_view import ToggleProgress
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import load, save, split_long
from typing import List, Optional, Dict, Set, Any


def print_dot(args, io: IO):
    tree = load(args.db)
    if args.n:
        tree.accept(ToggleOpenView())
    if args.p:
        tree.accept(ToggleProgress())
    if args.t:
        tree.accept(ToggleSwitchableView())
    io.write(dot_export(tree))


def print_md(args, io: IO):
    tree = load(args.db)
    if args.n:
        tree.accept(ToggleOpenView())
    if args.p:
        tree.accept(ToggleProgress())
    if args.t:
        tree.accept(ToggleSwitchableView())
    io.write(markdown_export(tree))


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
    parser_dot.add_argument("db", help="An existing file with goaltree.")
    parser_dot.set_defaults(func=print_dot)

    parser_dot = subparsers.add_parser("md")
    _flag(parser_dot, "-n", "Show closed goals (same as n key in the app)")
    _flag(parser_dot, "-p", "Show goal progress (same as p key in the app)")
    _flag(parser_dot, "-t", "Show only switchable goals (same as t key in app)")
    parser_dot.add_argument("db", help="An existing file with goaltree.")
    parser_dot.set_defaults(func=print_md)

    parser_migrate = subparsers.add_parser("migrate")
    parser_migrate.add_argument("db", help="An existing file with goaltree.")
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
    data = goals.q().slice(keys="open,name,edge,switchable")
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


def markdown_export(goals):
    data = goals.q().slice(keys="open,name,edge,switchable")
    output: List[str] = []
    for k, v in data.items():
        output.append(_format_md_row(k, v))
    return "\n".join(output)


def _format_md_row(goal_id: int, goal_attrs: Dict[str, Any]) -> str:
    open_status = " " if goal_attrs["open"] else "x"
    blockers: List[str] = [
        f"**{e[0]}**" for e in goal_attrs["edge"] if e[1] == EdgeType.BLOCKER
    ]
    blocked_status = "" if not blockers else f" (blocked by {', '.join(blockers)})"
    return f"* [{open_status}] **{goal_id}** {goal_attrs['name']}{blocked_status}"


def extract_subtree(source_goals: Graph, goal_id: int) -> Graph:
    root_goaltree: Goals = get_root(source_goals)
    source_data = root_goaltree.q().slice(keys="name,edge,open")
    assert goal_id in source_data.keys(), f"Cannot find goal with id {goal_id}"
    target_goals: Set[int] = set()
    goals_to_add: Set[int] = {goal_id}
    goals_data: GoalsData = []
    edges_data: EdgesData = []
    options_data: OptionsData = []
    while goals_to_add:
        goal = goals_to_add.pop()
        attrs = source_data[goal]
        target_goals.add(goal)
        goals_data.append((goal, attrs["name"], attrs["open"]))
        edges_data.extend((goal, target_, type_) for target_, type_ in attrs["edge"])
        goals_to_add.update(
            set(
                edge[0]
                for edge in attrs["edge"]
                if edge[1] == EdgeType.PARENT and edge[0] not in target_goals
            )
        )
    edges_data = [edge for edge in edges_data if edge[1] in target_goals]
    remap = {
        old: idx + 2
        for idx, old in enumerate(g for g in sorted(target_goals) if g != goal_id)
    }
    remap[goal_id] = Goals.ROOT_ID
    goals_data = [
        (remap[goal_id], name, is_open) for goal_id, name, is_open in goals_data
    ]
    edges_data = [
        (remap[source], remap[target], e_type) for source, target, e_type in edges_data
    ]
    return persistent_layers(Goals.build(goals_data, edges_data, options_data))
