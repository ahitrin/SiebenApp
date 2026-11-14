import shutil
from pathlib import Path

import pytest

from siebenapp import full_cli
from siebenapp.cli import fmt
from siebenapp.open_view import ToggleOpenView
from siebenapp.system import load
from tests.test_cli import verify_file

TEST_TEMPLATE_NEW = """
# {name}

## Given

{precondition}

## When

a user calls `si` with the following arguments:

```shell
si <file.db> {args}
```

## Then

an utility _{status}_ with the following output:
{stdout}

and the following error:
```
{stderr}
```

and file content will be the following:
```
{content_after}
```
"""


def format_quote(s: str) -> str:
    """Adds markdown quote sign (>) to every line of provided text."""
    return "\n".join("> " + l for l in s.splitlines())


def cleanup_stderr(s: str) -> str:
    candidates = {"_jb_pytest_runner.py": 24, "pytest": 6}
    for c, sp in candidates.items():
        if c not in s:
            continue
        s = s.replace(c, "si")
        s = s.replace(" " * sp, "  ")
    return s


def full_db_content(file_path):
    db = load(str(file_path))
    db.accept(ToggleOpenView())
    rr = db.q()
    db_content = "\n".join([fmt(rr, row, 60) for row in rr.rows])
    return db_content


@pytest.fixture
def mocks(monkeypatch, capsys, tmp_path):
    return monkeypatch, capsys, tmp_path


def target_file(tmp_path):
    return tmp_path / "si.db"


def _new_file_test(mocks, name: str, precondition: str, si_args: list[str]):
    monkeypatch, capsys, tmp_path = mocks
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("ROWS", "40")
    file_path = target_file(tmp_path)
    status = "passes"
    try:
        full_cli.main([str(file_path)] + [l.replace('"', "") for l in si_args])
    except SystemExit as sys_exit:
        status = f"exits with code {sys_exit.code}"
    out_err = capsys.readouterr()
    content_after = full_db_content(file_path)
    content = TEST_TEMPLATE_NEW.format(
        name=name,
        precondition=precondition,
        args=" ".join(si_args),
        status=status,
        stdout=format_quote(out_err.out),
        stderr=cleanup_stderr(out_err.err),
        content_after=content_after,
    )
    verify_file(content, ".md")


def test_new_success(mocks):
    _new_file_test(mocks, "Create new file","no file <file.db> exists",
                   ["new", '"Root subgoal"'])
