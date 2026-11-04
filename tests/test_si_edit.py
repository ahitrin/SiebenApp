import shutil
from pathlib import Path

import pytest

from siebenapp import full_cli
from siebenapp.cli import fmt
from siebenapp.open_view import ToggleOpenView
from siebenapp.system import load
from tests.test_cli import verify_file

TEST_TEMPLATE_EDIT = """
# {name}

## Given

we have a goal file with the following content:
```
{content_orig}
```

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

and goal file content will be the following:
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


def _edit_test(monkeypatch, capsys, tmp_path, name: str, si_args: list[str]):
    monkeypatch.setenv("COLUMNS", "80")
    src_path = Path(__file__).parent / "asset" / "si-example.db"
    file_path = tmp_path / "si.db"
    shutil.copy(src_path, file_path)
    content_orig = full_db_content(file_path)
    status = "passes"
    try:
        full_cli.main([str(file_path)] + [l.replace('"', "") for l in si_args])
    except SystemExit as sys_exit:
        status = f"exits with code {sys_exit.code}"
    out_err = capsys.readouterr()
    content_after = full_db_content(file_path)
    content = TEST_TEMPLATE_EDIT.format(
        name=name,
        content_orig=content_orig,
        args=" ".join(si_args),
        status=status,
        stdout=format_quote(out_err.out),
        stderr=cleanup_stderr(out_err.err),
        content_after=content_after,
    )
    verify_file(content, ".md")


def test_add(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch, capsys, tmp_path, "Add a goal", ["add", "5", '"New subgoal"']
    )


def test_add_error_incorrect_goal(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Add to an incorrect goal",
        ["add", "15", "failed"],
    )


@pytest.mark.skip("temporary disable due to environment-specific behavior")
def test_add_error_extra_description(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Add with extra arguments",
        ["add", "1", "extra", "arguments"],
    )


def test_add_error_missing_description(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch, capsys, tmp_path, "Add with missing description", ["add", "6"]
    )


def test_add_error_empty_description(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch, capsys, tmp_path, "Add with empty description", ["add", "6", '""']
    )


def test_insert_correct(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Correct insert",
        ["insert", "2", "5", '"Between A and A2"'],
    )


def test_insert_error_no_description(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Insert without goal description",
        ["insert", "2", "5"],
    )


def test_insert_error_empty_description(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Insert with empty goal description",
        ["insert", "2", "5", ""],
    )


@pytest.mark.skip("temporary disable due to environment-specific behavior")
def test_insert_error_extra_description(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Insert with extra description",
        ["insert", "2", "5", "I", "forgot", "to", "add", "quotes"],
    )


def test_insert_error_wrong_goal_order(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Insert: wrong goal order",
        ["insert", "5", "2", '"Create a loop with insert"'],
    )


def test_insert_error_incorrect_lower_goal(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Insert: incorrect lower goal",
        ["insert", "10", "2", '"Incorrect lower goal"'],
    )


def test_insert_error_incorrect_upper_goal(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Insert: incorrect lower goal",
        ["insert", "2", "10", '"Incorrect upper goal"'],
    )


def test_link_parent(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Link with parent/child relation",
        ["link", "2", "7", "parent"],
    )


def test_link_blocker(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Link with blocker relation",
        ["link", "7", "6", "blocker"],
    )


def test_link_relation(monkeypatch, capsys, tmp_path):
    _edit_test(
        monkeypatch,
        capsys,
        tmp_path,
        "Link with just relation",
        ["link", "6", "7", "relation"],
    )
