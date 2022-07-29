from argparse import ArgumentParser
from os import path
from siebenapp.cli import IO, ConsoleIO
from siebenapp.system import load, dot_export, save, extract_subtree
from typing import List, Optional


def print_dot(args, io: IO):
    tree = load(args.db)
    io.write(dot_export(tree))


def migrate(args, io: IO):
    goals = load(args.db)
    save(goals, args.db)


def extract(args, io: IO):
    tree = load(args.source_db).goaltree.goaltree
    assert not path.exists(args.target_db), f"File {args.target_db} already exists!"
    result = extract_subtree(tree, args.goal_id)
    save(result, args.target_db)


def main(argv: Optional[List[str]] = None, io: Optional[IO] = None):
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title="commands")

    parser_dot = subparsers.add_parser("dot")
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
