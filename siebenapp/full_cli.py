import argparse
import sys
from os import path

from siebenapp.autolink import ToggleAutoLink
from siebenapp.domain import (
    Add,
    Insert,
    ToggleLink,
    EdgeType,
    Graph,
    Rename,
    ToggleClose,
    Delete,
)
from siebenapp.filter_view import FilterBy
from siebenapp.goaltree import Goals
from siebenapp.layers import all_layers
from siebenapp.manage import markdown_export
from siebenapp.open_view import ToggleOpenView
from siebenapp.progress_view import ToggleProgress
from siebenapp.switchable_view import ToggleSwitchableView
from siebenapp.system import save, load_raw
from siebenapp.zoom_view import ToggleZoom


def new_file(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    description = args.description
    assert not path.exists(goal_file), f"File {goal_file} already exists!"
    db = Goals(description)
    save(all_layers(db), goal_file)


def view(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    show_closed = args.not_only_open
    show_top = args.top
    filter_line = args.filter
    zoom_root = args.zoom
    show_progress = args.progress
    db = load_raw(goal_file, use_selects=False)
    if show_closed:
        db.accept(ToggleOpenView())
    if show_top:
        db.accept(ToggleSwitchableView())
    if show_progress:
        db.accept(ToggleProgress())
    if filter_line:
        db.accept(FilterBy(filter_line))
    if zoom_root:
        db.accept(ToggleZoom(zoom_root))
    print(markdown_export(db))


def _process_event(goal_file: str, event, check_fn=None) -> None:
    errors: list[str] = []
    db = load_raw(goal_file, errors.append)

    if check_fn is not None:
        try:
            check_fn(db)
        except ValueError as err:
            print(str(err))
            exit(1)

    db.accept(event)
    if errors:
        for e in errors:
            print(e)
        exit(1)
    else:
        save(db, goal_file)


def add(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    parent = args.parent
    description = args.description
    _process_event(goal_file, Add(description, parent))


def insert(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    description = args.description
    _process_event(goal_file, Insert(description, first, second))


def link(args: argparse.Namespace) -> None:
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


def unlink(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    link_type = [EdgeType.PARENT]

    def check(db: Graph):
        rr = db.q()
        parent_row = rr.by_id(first)
        e_types = {e_type for g_id, e_type in parent_row.edges if g_id == second}
        if e_types:
            link_type[0] = e_types.pop()
        else:
            raise ValueError(f"Link between goals {first} and {second} dosen't exist")

    _process_event(goal_file, ToggleLink(first, second, link_type[0]), check)


def rename(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    description = args.description
    _process_event(goal_file, Rename(description, goal_id))


def autolink(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    tag = args.tag
    _process_event(goal_file, ToggleAutoLink(tag, goal_id))


def close_goal(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id

    def check(db):
        rr = db.q()
        if goal_id not in rr.index:
            raise ValueError(f"Goal {goal_id} is not open")
        if not rr.by_id(goal_id).is_open:
            raise ValueError(f"Goal {goal_id} is not open")

    _process_event(goal_file, ToggleClose(goal_id), check)


def open_goal(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id

    def check(db):
        rr = db.q()
        if goal_id not in rr.index:
            # Just ignore this case
            return
        if rr.by_id(goal_id).is_open:
            raise ValueError(f"Goal {goal_id} is already open")

    _process_event(goal_file, ToggleClose(goal_id), check)


def delete_goal(args: argparse.Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id

    if args.force:
        _process_event(goal_file, Delete(goal_id))
    else:
        raise ValueError(
            f"Goal {goal_id} will be removed only if '--force' flag is set."
        )


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description=(
            "SiebenApp is a CLI tool for managing goal trees. It allows you to "
            "define, organize, and visualize project goals and their relationships."
        )
    )
    parser.add_argument("goal_file")
    subparsers = parser.add_subparsers(title="commands")

    parser_new = subparsers.add_parser("new", description="Create a new project file.")
    parser_new.add_argument(
        "description",
        help="Description of the root goal. Write here what do you need to do.",
    )
    parser_new.set_defaults(func=new_file)

    parser_view = subparsers.add_parser(
        "view",
        description="View a whole goal tree or only its part. By default, only open goals are shown.",
    )
    parser_view.add_argument(
        "-n",
        "--not-only-open",
        required=False,
        action="store_true",
        help="Show already closed goals in addition to open ones.",
    )
    parser_view.add_argument(
        "-t",
        "--top",
        required=False,
        action="store_true",
        help="Show only actionable ('top') goals.",
    )
    parser_view.add_argument(
        "-p",
        "--progress",
        required=False,
        action="store_true",
        help="Show goals progress or statistics.",
    )
    parser_view.add_argument(
        "-f",
        "--filter",
        required=False,
        help="Only show goals containing a provided substring.",
    )
    parser_view.add_argument(
        "-z",
        "--zoom",
        required=False,
        type=int,
        help="Zoom to a given subgoal (by its ID). Only show its subgoals and related items.",
    )
    parser_view.set_defaults(func=view)

    parser_add = subparsers.add_parser(
        "add", description="Add a new goal under a specific parent"
    )
    parser_add.add_argument("parent", type=int, help="The ID of the parent goal")
    parser_add.add_argument("description", help="The description text of the new goal")
    parser_add.set_defaults(func=add)

    parser_insert = subparsers.add_parser(
        "insert",
        description="Insert a new goal between two already existing ('lower' and 'upper') ones,",
    )
    parser_insert.add_argument(
        "first",
        type=int,
        help="ID of the 'lower' goal. An inserted goal will be its child.",
    )
    parser_insert.add_argument(
        "second",
        type=int,
        help="ID of the 'upper' goal. An inserted goal will be its parent.",
    )
    parser_insert.add_argument(
        "description", help="The description text of the new goal."
    )
    parser_insert.set_defaults(func=insert)

    parser_link = subparsers.add_parser(
        "link",
        description="Link two goals ('first'->'second') by their IDs with a specific link type, or change a type of an already existing link.",
    )
    parser_link.add_argument("first", type=int, help="ID of a 'lower' goal to link.")
    parser_link.add_argument("second", type=int, help="ID of an 'upper' goal to link.")
    parser_link.add_argument(
        "link_type",
        type=lambda s: EdgeType[s.upper()],
        choices=list(EdgeType),
        help="New link type.",
    )
    parser_link.set_defaults(func=link)

    parser_unlink = subparsers.add_parser(
        "unlink",
        description="Remove an already existing link between 'first' and 'second' goals.",
    )
    parser_unlink.add_argument(
        "first",
        type=int,
        help="A 'lower' goal for the link (say, parent or blocked one).",
    )
    parser_unlink.add_argument(
        "second",
        type=int,
        help="An 'upper' goal for the link (e.g., child or blocker).",
    )
    parser_unlink.set_defaults(func=unlink)

    parser_rename = subparsers.add_parser(
        "rename", description="Change description of a given goal."
    )
    parser_rename.add_argument("goal_id", type=int, help="Goal ID.")
    parser_rename.add_argument("description", help="New goal description.")
    parser_rename.set_defaults(func=rename)

    parser_autolink = subparsers.add_parser(
        "autolink",
        description="Automatically bind all new or renamed goals containing given tag to this goal. They will become children of a given goal rather than of their original parents.",
    )
    parser_autolink.add_argument(
        "goal_id", type=int, help="ID of an autolink parent goal."
    )
    parser_autolink.add_argument("tag", help="Text tag to match.")
    parser_autolink.set_defaults(func=autolink)

    parser_close = subparsers.add_parser("close", description="Close an open goal.")
    parser_close.add_argument("goal_id", type=int, help="Goal ID.")
    parser_close.set_defaults(func=close_goal)

    parser_open = subparsers.add_parser(
        "open", description="Re-open already closed goal."
    )
    parser_open.add_argument("goal_id", type=int, help="Goal ID.")
    parser_open.set_defaults(func=open_goal)

    parser_delete = subparsers.add_parser("delete", description="Delete a goal.")
    parser_delete.add_argument("goal_id", type=int, help="Goal ID.")
    parser_delete.add_argument(
        "-f", "--force", action="store_true", help="Really perform a deletion."
    )
    parser_delete.set_defaults(func=delete_goal)

    if "--help" in sys.argv or "-h" in sys.argv:
        # Print the main parser help first
        parser.print_help()
        print("\n" + "=" * 50 + "\nCOMMAND DETAILS:\n" + "=" * 50)

        # Iterate through actions to find subparsers
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for choice, subparser in action.choices.items():
                    print(f"\n--- Command '{choice}' ---")
                    # format_help() returns the help message as a string
                    print(subparser.format_help())

        sys.exit(0)

    args = parser.parse_args(argv)
    if "func" in dir(args):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    # For debugging
    main(sys.argv[1:])
