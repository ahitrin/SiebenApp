from typing import List

from approvaltests import verify, Options  # type: ignore
from approvaltests.reporters.generic_diff_reporter import GenericDiffReporter  # type: ignore

from siebenapp.cli import IO, update_message, loop
from siebenapp.system import load


class DummyIO(IO):
    def __init__(self, commands: List[str], log: List[str]):
        super().__init__()
        self.commands = commands
        self.log = log

    def write(self, text: str, *args) -> None:
        self.log.append(" ".join([text, *args]))

    def read(self) -> str:
        if self.commands:
            command = self.commands.pop(0)
            self.log.append(f"> {command}\n")
            return command
        self.log.append("*USER BREAK*")
        raise EOFError("Commands list is empty")


def test_simple_scenario():
    log = []
    commands = [
        "r Approval testing",
        "a Measure coverage",
        "2",
        "a Build simple test",
        "3",
        "c",
    ]
    io = DummyIO(commands, log)
    db_name = ":memory:"
    goals = load(db_name, update_message)
    loop(io, goals, db_name)
    verify(
        "\n".join(log),
        options=Options().with_reporter(GenericDiffReporter.create("/usr/bin/diff")),
    )
