import shutil
import sys
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


@pytest.fixture
def mocks(monkeypatch, capsys, tmp_path):
    return monkeypatch, capsys, tmp_path


def _edit_test(mocks, name: str, si_args: list[str]):
    monkeypatch, capsys, tmp_path = mocks
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("ROWS", "40")
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


def test_add(mocks):
    _edit_test(mocks, "Add a goal", ["add", "5", '"New subgoal"'])


def test_add_error_incorrect_goal(mocks):
    _edit_test(mocks, "Add to an incorrect goal", ["add", "15", "failed"])


@pytest.mark.skip("temporary disable due to environment-specific behavior")
def test_add_error_extra_description(mocks):
    _edit_test(mocks, "Add with extra arguments", ["add", "1", "extra", "arguments"])


def test_add_error_missing_description(mocks):
    _edit_test(mocks, "Add with missing description", ["add", "6"])


def test_add_error_empty_description(mocks):
    _edit_test(mocks, "Add with empty description", ["add", "6", '""'])


def test_insert_correct(mocks):
    _edit_test(mocks, "Correct insert", ["insert", "2", "5", '"Between A and A2"'])


def test_insert_error_no_description(mocks):
    _edit_test(mocks, "Insert without goal description", ["insert", "2", "5"])


def test_insert_error_empty_description(mocks):
    _edit_test(mocks, "Insert with empty goal description", ["insert", "2", "5", ""])


@pytest.mark.skip("temporary disable due to environment-specific behavior")
def test_insert_error_extra_description(mocks):
    _edit_test(
        mocks,
        "Insert with extra description",
        ["insert", "2", "5", "I", "forgot", "to", "add", "quotes"],
    )


def test_insert_error_wrong_goal_order(mocks):
    _edit_test(
        mocks,
        "Insert: wrong goal order",
        ["insert", "5", "2", '"Create a loop with insert"'],
    )


def test_insert_error_incorrect_lower_goal(mocks):
    _edit_test(
        mocks,
        "Insert: incorrect lower goal",
        ["insert", "10", "2", '"Incorrect lower goal"'],
    )


def test_insert_error_incorrect_upper_goal(mocks):
    _edit_test(
        mocks,
        "Insert: incorrect lower goal",
        ["insert", "2", "10", '"Incorrect upper goal"'],
    )


def test_link_parent(mocks):
    _edit_test(mocks, "Link with parent/child relation", ["link", "2", "7", "parent"])


def test_link_blocker(mocks):
    _edit_test(mocks, "Link with blocker relation", ["link", "7", "6", "blocker"])


def test_link_relation(mocks):
    _edit_test(mocks, "Link with just relation", ["link", "6", "7", "relation"])


def test_link_change_type(mocks):
    _edit_test(mocks, "Change link type", ["link", "7", "5", "relation"])


@pytest.mark.skipif(
    list(sys.version_info)[:2] == [3, 12],
    reason="Python 3.12 is very special in help formatting",
)
def test_link_error_new_link_of_unknown_type(mocks):
    _edit_test(mocks, "New link of unknown type", ["link", "1", "5", "unknown"])


@pytest.mark.skipif(
    list(sys.version_info)[:2] != [3, 12],
    reason="Python 3.12 is very special in help formatting",
)
def test_link_error_new_link_of_unknown_type_py312(mocks):
    _edit_test(mocks, "New link of unknown type", ["link", "1", "5", "unknown"])


@pytest.mark.skipif(
    list(sys.version_info)[:2] == [3, 12],
    reason="Python 3.12 is very special in help formatting",
)
def test_link_error_change_type_to_unknown(mocks):
    _edit_test(mocks, "Unknown link type replaces known", ["link", "7", "5", "unknown"])


@pytest.mark.skipif(
    list(sys.version_info)[:2] != [3, 12],
    reason="Python 3.12 is very special in help formatting",
)
def test_link_error_change_type_to_unknown_py312(mocks):
    _edit_test(mocks, "Unknown link type replaces known", ["link", "7", "5", "unknown"])


def test_link_error_create_loop(mocks):
    _edit_test(mocks, "New link creates a loop", ["link", "9", "1", "relation"])


def test_link_error_incorrect_lower_goal(mocks):
    _edit_test(mocks, "Link: incorrect lower goal", ["link", "10", "5", "blocker"])


def test_link_error_incorrect_upper_goal(mocks):
    _edit_test(mocks, "Link: incorrect upper goal", ["link", "5", "10", "blocker"])


def test_link_error_incorrect_both_goals(mocks):
    _edit_test(mocks, "Link: incorrect both goals", ["link", "15", "10", "relation"])


def test_unlink_parent(mocks):
    _edit_test(mocks, "Correct unlink: parent relation", ["unlink", "8", "9"])


def test_unlink_blocker(mocks):
    _edit_test(mocks, "Correct unlink: blocker relation", ["unlink", "7", "5"])


def test_unlink_relation(mocks):
    _edit_test(mocks, "Correct unlink: relation", ["unlink", "2", "9"])


def test_unlink_relation_with_closed_upper_goal(mocks):
    _edit_test(mocks, "Correct unlink with closed upper goal", ["unlink", "9", "4"])


def test_unlink_last_parent(mocks):
    _edit_test(mocks, "Unlink: remove last parent", ["unlink", "1", "3"])


def test_unlink_error_no_existing_link(mocks):
    _edit_test(mocks, "Unlink error: link doesn't exist", ["unlink", "6", "5"])


def test_unlink_error_incorrect_lower_goal(mocks):
    _edit_test(mocks, "Unlink error: incorrect lower goal", ["unlink", "11", "5"])


def test_unlink_error_incorrect_upper_goal(mocks):
    _edit_test(mocks, "Unlink error: incorrect upper goal", ["unlink", "5", "11"])


def test_unlink_error_incorrect_both_goals(mocks):
    _edit_test(mocks, "Unlink error: incorrect both goals", ["unlink", "13", "11"])


def test_close_correct(mocks):
    _edit_test(mocks, "Correct close of an open goal", ["close", "6"])


def test_close_error_cannot_be_closed(mocks):
    _edit_test(mocks, "Closing a goal that cannot be closed yet", ["close", "3"])


def test_close_error_already_closed(mocks):
    _edit_test(mocks, "Closing an already closed goal", ["close", "4"])


def test_close_error_incorrect_goal(mocks):
    _edit_test(mocks, "Close goal that doesn't exist", ["close", "77"])


def test_open_correct(mocks):
    _edit_test(mocks, "Correct goal re-open", ["open", "4"])


def test_open_error_incorrect_goal(mocks):
    _edit_test(mocks, "Re-open goal that doesn't exist", ["open", "44"])


def test_open_error_already_open(mocks):
    _edit_test(mocks, "Re-open goal that's not closed", ["open", "5"])
