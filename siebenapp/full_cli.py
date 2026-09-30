from argparse import ArgumentParser, Namespace
from os import path

from siebenapp.domain import Add, Insert, ToggleLink, EdgeType, Graph
from siebenapp.goaltree import Goals
from siebenapp.layers import all_layers
from siebenapp.manage import markdown_export
from siebenapp.open_view import ToggleOpenView
from siebenapp.progress_view import ToggleProgress
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import save, load_raw


def new_file(args: Namespace) -> None:
    goal_file = args.goal_file
    description = args.description
    assert not path.exists(goal_file), f"File {goal_file} already exists!"
    db = Goals(description)
    save(all_layers(db), goal_file)


def view(args: Namespace) -> None:
    goal_file = args.goal_file
    show_closed = args.not_only_open
    show_top = args.top
    show_progress = args.progress
    db = load_raw(goal_file)
    if show_closed:
        db.accept(ToggleOpenView())
    if show_top:
        db.accept(ToggleSwitchableView())
    if show_progress:
        db.accept(ToggleProgress())
    print(markdown_export(db))


def _process_event(goal_file: str, event, check_fn=None) -> None:
    errors: list[str] = []
    db = load_raw(goal_file, errors.append)

    if check_fn is not None:
        try:
            check_fn(db)
        except ValueError as e:
            print(str(e))
            exit(1)

    db.accept(event)
    if errors:
        for e in errors:
            print(e)
        exit(1)
    else:
        save(db, goal_file)


def add(args: Namespace) -> None:
    goal_file = args.goal_file
    parent = args.parent
    description = args.description
    _process_event(goal_file, Add(description, parent))


def insert(args: Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    description = args.description
    _process_event(goal_file, Insert(description, first, second))


def link(args: Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    link_type = args.link_type

    def check(db: Graph):
        rr = db.q()
        parent_row = rr.by_id(first)
        if any(
            [
                1
                for g_id, e_type in parent_row.edges
                if g_id == second and e_type == link_type
            ]
        ):
            raise ValueError(f"Link between goals {first} and {second} already exists")

    _process_event(goal_file, ToggleLink(first, second, link_type), check)


def unlink(args: Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    link_type = EdgeType.PARENT

    def check(db: Graph):
        rr = db.q()
        parent_row = rr.by_id(first)
        e_types = {e_type for g_id, e_type in parent_row.edges if g_id == second}
        if e_types:
            unlink.link_type = e_types.pop()
        else:
            raise ValueError(f"Link between goals {first} and {second} dosen't exist")

    _process_event(goal_file, ToggleLink(first, second, link_type), check)


def rename(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    description = args.description
    print(f'file: {goal_file}, first={goal_id}. description="{description}"')


def autolink(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    tag = args.tag
    print(f'file: {goal_file}, goal_id={goal_id}. tag="{tag}"')


def close_goal(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    print(f"file: {goal_file}, goal_id={goal_id}")


def open_goal(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    print(f"file: {goal_file}, goal_id={goal_id}")


def delete_goal(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    print(f"file: {goal_file}, goal_id={goal_id}")


def main(argv: list[str] | None = None):
    parser = ArgumentParser()
    parser.add_argument("goal_file")
    subparsers = parser.add_subparsers(title="commands")

    parser_new = subparsers.add_parser("new")
    parser_new.add_argument("description")
    parser_new.set_defaults(func=new_file)

    parser_view = subparsers.add_parser("view")
    parser_view.add_argument(
        "-n", "--not-only-open", required=False, action="store_true"
    )
    parser_view.add_argument("-t", "--top", required=False, action="store_true")
    parser_view.add_argument("-p", "--progress", required=False, action="store_true")
    # parser_view.add_argument("-f")  # filter [by what]
    # parser_view.add_argument("-z")  # zoom [on what]
    parser_view.set_defaults(func=view)

    parser_add = subparsers.add_parser("add")
    parser_add.add_argument("parent", type=int)
    parser_add.add_argument("description")
    parser_add.set_defaults(func=add)

    parser_insert = subparsers.add_parser("insert")
    parser_insert.add_argument("first", type=int)
    parser_insert.add_argument("second", type=int)
    parser_insert.add_argument("description")
    parser_insert.set_defaults(func=insert)

    parser_link = subparsers.add_parser("link")
    parser_link.add_argument("first", type=int)
    parser_link.add_argument("second", type=int)
    parser_link.add_argument(
        "link_type",
        type=lambda s: EdgeType[s.upper()],
        choices=list(EdgeType),
        default=EdgeType.PARENT,
    )
    parser_link.set_defaults(func=link)

    parser_unlink = subparsers.add_parser("unlink")
    parser_unlink.add_argument("first", type=int)
    parser_unlink.add_argument("second", type=int)
    parser_unlink.set_defaults(func=unlink)

    parser_rename = subparsers.add_parser("rename")
    parser_rename.add_argument("goal_id", type=int)
    parser_rename.add_argument("description")
    parser_rename.set_defaults(func=rename)

    parser_autolink = subparsers.add_parser("autolink")
    parser_autolink.add_argument("goal_id", type=int)
    parser_autolink.add_argument("tag")
    parser_autolink.set_defaults(func=autolink)

    parser_close = subparsers.add_parser("close")
    parser_close.add_argument("goal_id", type=int)
    parser_close.set_defaults(func=close_goal)

    parser_open = subparsers.add_parser("open")
    parser_open.add_argument("goal_id", type=int)
    parser_open.set_defaults(func=open_goal)

    parser_delete = subparsers.add_parser("delete")
    parser_delete.add_argument("goal_id", type=int)
    parser_delete.set_defaults(func=delete_goal)

    args = parser.parse_args(argv)
    if "func" in dir(args):
        args.func(args)
    else:
        parser.print_help()
