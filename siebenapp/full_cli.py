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
                             default="--parent")
    parser_link.set_defaults(func=link)

    args = parser.parse_args(argv)
    if "func" in dir(args):
        args.func(args)
    else:
        parser.print_help()
