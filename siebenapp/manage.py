from argparse import ArgumentParser, Namespace
from html import escape
from operator import attrgetter
from os import path

from siebenapp.cli import IO, ConsoleIO
from siebenapp.domain import EdgeType, Graph, RenderRow, GoalId, RenderResult
from siebenapp.goaltree import Goals, GoalsData, EdgesData, OptionsData
from siebenapp.layers import get_root, persistent_layers, all_layers
from siebenapp.open_view import ToggleOpenView
from siebenapp.progress_view import ToggleProgress
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import load, save, split_long


def print_dot(args: Namespace, io: IO) -> None:
    tree = load(args.db)
    if args.n:
        tree.accept(ToggleOpenView())
    if args.p:
        tree.accept(ToggleProgress())
    if args.t:
        tree.accept(ToggleSwitchableView())
    io.write(dot_export(tree))


def print_md(args: Namespace, io: IO) -> None:
    tree = load(args.db)
    if args.n:
        tree.accept(ToggleOpenView())
    if args.p:
        tree.accept(ToggleProgress())
    if args.t:
        tree.accept(ToggleSwitchableView())
    io.write(markdown_export(tree))


def migrate(args: Namespace, io: IO) -> None:
    goals = load(args.db)
    save(goals, args.db)


def extract(args: Namespace, io: IO) -> None:
    tree = load(args.source_db).goaltree.goaltree
    assert not path.exists(args.target_db), f"File {args.target_db} already exists!"
    result = extract_subtree(tree, args.goal_id)
    save(result, args.target_db)


def merge(args: Namespace, io: IO) -> None:
    sources: list[str] = args.source_db
    assert not path.exists(args.target_db), f"File {args.target_db} already exists!"
    assert (
        len(sources) >= 2
    ), f"There should be at least 2 files to merge, but I see {len(sources)}."
    for source_db in sources:
        assert path.exists(source_db), f"File {source_db} is missing."

    merged_db = Goals("Merged")
    delta = 1
    for source_db in sources:
        source_root = get_root(load(source_db), Goals)
        merged_db.goals |= {
            goal_id + delta: name for goal_id, name in source_root.goals.items()
        }
        merged_db.edges |= {
            (edge[0] + delta, edge[1] + delta): edge_type
            for edge, edge_type in source_root.edges.items()
        }
        merged_db.edges[Goals.ROOT_ID, min(source_root.goals.keys()) + delta] = (
            EdgeType.PARENT
        )
        merged_db.closed.update({goal_id + delta for goal_id in source_root.closed})
        delta = max(merged_db.goals.keys())

    save(all_layers(merged_db), args.target_db)


def _flag(parser: ArgumentParser, key: str, description: str) -> None:
    parser.add_argument(key, required=False, action="store_true", help=description)


def main(argv: list[str] | None = None, io: IO | None = None) -> None:
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
        "This file will not be modified during the operation. "
        "You may/should do it manually.",
    )
    parser_extract.add_argument(
        "target_db",
        help="A new file to be created. It will contain a result of extraction. "
        "Only subgoals and edges are extracted, no zoom and/or autolink data "
        "is inherited.",
    )
    parser_extract.add_argument(
        "goal_id",
        type=int,
        help="An id of the goal that should be set as a root goal of a new goaltree. "
        "All of its subgoals will be copied too (but not blockers). "
        "The simplest way to find a real id of a goal is to run `sieben-manage dot` "
        "on the source file.",
    )
    parser_extract.set_defaults(func=extract)

    parser_merge = subparsers.add_parser("merge")
    parser_merge.add_argument(
        "target_db",
        help="File where merged results will be written into. "
        "Should not exist beforhand.",
    )
    parser_merge.add_argument(
        "source_db", nargs="+", help="Files to merge (at least 2)."
    )
    parser_merge.set_defaults(func=merge)

    args = parser.parse_args(argv)
    io = io or ConsoleIO("> ")
    if "func" in dir(args):
        args.func(args, io)
    else:
        parser.print_help()


def _format_name(row: RenderRow) -> str:
    goal_name = escape(row.name)
    label = split_long(
        f"{row.goal_id}: {goal_name}"
        if isinstance(row.goal_id, int) and row.goal_id >= 0
        else f"{goal_name}"
    )
    attrs: list[str] = [f"{k}: {split_long(v)}" for k, v in row.attrs.items()]
    return '"' + "\n".join([label] + attrs) + '"'


def dot_export(goals: Graph) -> str:
    render_result = goals.q()
    node_lines = []
    edge_lines = []
    for row in sorted(render_result.rows, key=attrgetter("goal_id")):
        attributes = {
            "label": _format_name(row),
            "color": "red" if row.is_open else "green",
        }
        if row.is_switchable and row.is_open:
            attributes["style"] = "bold"
        attributes_str = ", ".join(
            f"{k}={attributes[k]}"
            for k in ["label", "color", "style", "fillcolor"]
            if k in attributes and attributes[k]
        )
        node_lines.append(f"{row.goal_id} [{attributes_str}];")
        for edge in row.edges:
            color = "black" if render_result.by_id(edge[0]).is_open else "gray"
            line_attrs = f"color={color}"
            if edge[1] == EdgeType.BLOCKER:
                line_attrs += ", style=dashed"
            elif edge[1] == EdgeType.RELATION:
                line_attrs += ", style=dotted"
            edge_lines.append(f"{edge[0]} -> {row.goal_id} [{line_attrs}];")
    body = "\n".join(node_lines + edge_lines)
    return f"digraph g {{\nnode [shape=box];\n{body}\n}}"


def markdown_export(goals: Graph) -> str:
    render_result = goals.q()
    all_ids = {r.goal_id for r in render_result.rows}
    non_roots = {
        e[0] for r in render_result.rows for e in r.edges if e[1] == EdgeType.PARENT
    }
    roots = all_ids.difference(non_roots)
    output: list[str] = []
    for root_id in sorted(list(roots)):
        output.extend(_md_tree(render_result, root_id, 0))
    return "\n".join(output)


def _md_tree(render_result: RenderResult, root_id: GoalId, shift: int) -> list[str]:
    row = render_result.by_id(root_id)
    result = [_format_md_row(render_result, row, shift)]
    for edge in row.edges:
        if edge[1] == EdgeType.PARENT:
            result.extend(_md_tree(render_result, edge[0], shift + 1))
    return result


def _format_md_row(render_result: RenderResult, row: RenderRow, shift: int) -> str:
    is_open = " " if row.is_open else "x"
    blockers: list[str] = []
    relations: list[str] = []
    for e in row.edges:
        if e[1] == EdgeType.BLOCKER and render_result.by_id(e[0]).is_open:
            blockers.append(f"**{e[0]}**")
        elif e[1] == EdgeType.RELATION:
            relations.append(f"**{e[0]}**")
    blocked = "" if not blockers else f"blocked by {', '.join(blockers)}"
    related = "" if not relations else f"related to {', '.join(relations)}"
    extras = [s for s in [blocked, related] if s]
    extras_formatted = "" if not extras else f" ({', '.join(extras)})"
    attrs = (
        ""
        if not row.attrs
        else f" [{','.join(f'{k}: {row.attrs[k]}' for k in sorted(row.attrs.keys()))}]"
    )
    spaces = " " * shift * 2
    return (
        f"{spaces}* [{is_open}] **{row.goal_id}** {row.name}{extras_formatted}{attrs}"
    )


def extract_subtree(source_goals: Graph, goal_id: int) -> Graph:
    root_goaltree: Goals = get_root(source_goals, Goals)
    render_result = root_goaltree.q()
    assert (
        render_result.by_id(goal_id) is not None
    ), f"Cannot find goal with id {goal_id}"
    target_goals: set[GoalId] = set()
    goals_to_add: set[GoalId] = {goal_id}
    goals_data: GoalsData = []
    edges_data: EdgesData = []
    options_data: OptionsData = []
    while goals_to_add:
        goal = goals_to_add.pop()
        row = render_result.by_id(goal)
        target_goals.add(goal)
        goals_data.append((int(goal), row.name, row.is_open))
        edges_data.extend(
            (int(goal), int(target_), type_) for target_, type_ in row.edges
        )
        goals_to_add.update(
            {goal for goal, edge_type in row.edges if edge_type == EdgeType.PARENT}
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
    return persistent_layers(
        Goals.build(goals_data, edges_data, options_data), options_data
    )
