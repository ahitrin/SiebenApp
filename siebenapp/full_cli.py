from argparse import ArgumentParser, Namespace


def new_file(args: Namespace) -> None:
    pass


def view(args: Namespace) -> None:
    pass


def add(args: Namespace) -> None:
    pass


def insert(args: Namespace) -> None:
    pass


def link(args: Namespace) -> None:
    pass


def unlink(args: Namespace) -> None:
    pass


def rename(args: Namespace) -> None:
    pass


def autolink(args: Namespace) -> None:
    pass


def close_goal(args: Namespace) -> None:
    pass


def open_goal(args: Namespace) -> None:
    pass


def delete_goal(args: Namespace) -> None:
    pass


def main(argv: list[str] | None = None):
    parser = ArgumentParser()
    parser.add_argument("goal_file")
    subparsers = parser.add_subparsers(title="commands")

    parser_new = subparsers.add_parser("new")
    parser_new.add_argument("description")
    parser_new.set_defaults(func=new_file)

    parser_view = subparsers.add_parser("view")
    parser_view.add_argument("-n")  # open
    parser_view.add_argument("-t")  # switchable
    parser_view.add_argument("-p")  # progress
    #parser_view.add_argument("-f")  # filter [by what]
    #parser_view.add_argument("-z")  # zoom [on what]
    parser_view.set_defaults(func=view)

    parser_add = subparsers.add_parser("add")
    parser_add.add_argument("parent")
    parser_add.add_argument("description")
    parser_add.set_defaults(func=add)

    parser_insert = subparsers.add_parser("insert")
    parser_insert.add_argument("parent")
    parser_insert.add_argument("child")
    parser_insert.add_argument("description")
    parser_insert.set_defaults(func=insert)

    parser_link = subparsers.add_parser("link")
    parser_link.add_argument("first")
    parser_link.add_argument("second")
    parser_link.add_argument("link_type",
                             default="--parent")    # TODO: --block --relate
    parser_link.set_defaults(func=link)

    parser_unlink = subparsers.add_parser("unlink")
    parser_unlink.add_argument("first")
    parser_unlink.add_argument("second")
    parser_unlink.set_defaults(func=unlink)

    parser_rename = subparsers.add_parser("rename")
    parser_rename.add_argument("goal_id")
    parser_rename.add_argument("description")
    parser_rename.set_defaults(func=rename)

    parser_autolink = subparsers.add_parser("autolink")
    parser_autolink.add_argument("goal_id")
    parser_autolink.add_argument("marker")
    parser_autolink.set_defaults(func=autolink)

    parser_close = subparsers.add_parser("close")
    parser_close.add_argument("goal_id")
    parser_autolink.set_defaults(func=close_goal)

    parser_open = subparsers.add_parser("open")
    parser_open.add_argument("goal_id")
    parser_open.set_defaults(func=open_goal)

    args = parser.parse_args(argv)
    if "func" in dir(args):
        args.func(args)
    else:
        parser.print_help()
