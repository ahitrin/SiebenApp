from pathlib import Path

import pytest

from siebenapp import full_cli
from siebenapp.cli import fmt
from siebenapp.open_view import ToggleOpenView
from siebenapp.system import load
from tests.test_cli import verify_file

TEST_TEMPLATE = """
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


def _view_test(capsys, name: str, si_args: list[str]):
    file_path = Path(__file__).parent / "asset" / "si-example.db"
    db = load(str(file_path))
    db.accept(ToggleOpenView())
    rr = db.q()
    content_orig = "\n".join([fmt(rr, row, 60) for row in rr.rows])
    status = "passes"
    try:
        full_cli.main([str(file_path), "view"] + [l.replace('"', "") for l in si_args])
    except SystemExit as sys_exit:
        status = f"exits with code {sys_exit.code}"
    out_err = capsys.readouterr()
    content = TEST_TEMPLATE.format(
        name=name,
        content_orig=content_orig,
        args=" ".join(si_args),
        status=status,
        stdout=format_quote(out_err.out),
        stderr=cleanup_stderr(out_err.err),
    )
    verify_file(content, ".md")


def test_default_view(capsys):
    _view_test(capsys, "Default view", [])


def test_show_closed(capsys):
    _view_test(capsys, "Show closed", ["-n"])


def test_show_top(capsys):
    _view_test(capsys, "Show top", ["-t"])


def test_show_progress(capsys):
    _view_test(capsys, "Show progress", ["-p"])


def test_show_filter(capsys):
    _view_test(capsys, "Show filter", ["-f", "none"])


def test_show_zoom(capsys):
    _view_test(capsys, "Show zoom", ["-z", "2"])


def test_closed_filter(capsys):
    _view_test(capsys, "Closed + filter", ["-n", "-f", '"goal a"'])


def test_zoom_progress(capsys):
    _view_test(capsys, "Zoom + progress", ["-z", "3", "-p"])


def test_closed_top(capsys):
    _view_test(capsys, "Closed + top", ["-n", "-t"])


def test_progress_top(capsys):
    _view_test(capsys, "Progress + top", ["-p", "-t"])


def test_filter_zoom(capsys):
    _view_test(capsys, "Filter + zoom", ["-f", "A2", "-z", "3"])


def test_progress_closed_zoom(capsys):
    _view_test(capsys, "Progress + closed + zoom", ["-p", "-n", "-z", "2"])


def test_top_zoom_filter(capsys):
    _view_test(capsys, "Top + zoom + filter", ["-t", "-z", "8", "-f", "later"])


@pytest.mark.skip("unstable behavior, depends on screen width")
def test_error_extra_filter(capsys):
    _view_test(capsys, "Error: extra filter", ["-f", "goal", "a"])


def test_error_zoom_wrong_goal_id(capsys):
    _view_test(capsys, "Error: wrong goal id on zoom", ["-z", "12"])
