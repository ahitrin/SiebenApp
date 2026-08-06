from argparse import ArgumentParser, Namespace


def new_file(args: Namespace) -> None:
    goal_file = args.goal_file
    description = args.description
    print(f'file: {goal_file}, description: "{description}"')


def view(args: Namespace) -> None:
    goal_file = args.goal_file
    show_closed = args.not_only_open
    show_top = args.top
    show_progress = args.progress
    print(f"file: {goal_file}, cls={show_closed}, top={show_top}, prog={show_progress}")


def add(args: Namespace) -> None:
    goal_file = args.goal_file
    parent = args.parent
    description = args.description
    print(f'file: {goal_file}, parent: {parent}, description: "{description}"')


def insert(args: Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    description = args.description
    print(f'file: {goal_file}, first={first}, second={second}, description: "{description}"')


def link(args: Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    link_type = args.link_type
    print(f'file: {goal_file}, first={first}, second={second}, type: "{link_type}"')


def unlink(args: Namespace) -> None:
    goal_file = args.goal_file
    first = args.first
    second = args.second
    print(f'file: {goal_file}, first={first}, second={second}"')


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
    print(f'file: {goal_file}, goal_id={goal_id}')


def open_goal(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    print(f'file: {goal_file}, goal_id={goal_id}')


def delete_goal(args: Namespace) -> None:
    goal_file = args.goal_file
    goal_id = args.goal_id
    print(f'file: {goal_file}, goal_id={goal_id}')


def main(argv: list[str] | None = None):
    parser = ArgumentParser()
    parser.add_argument("goal_file")
    subparsers = parser.add_subparsers(title="commands")

    parser_new = subparsers.add_parser("new")
    parser_new.add_argument("description")
    parser_new.set_defaults(func=new_file)

    parser_view = subparsers.add_parser("view")
    parser_view.add_argument("-n", "--not-only-open", required=False, action="store_true")
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
    parser_link.add_argument("link_type", default="--parent")  # TODO: --block --relate
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
