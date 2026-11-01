from pathlib import Path
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
{stderr}
"""


def format_quote(s: str) -> str:
    return "\n".join("> " + l for l in s.splitlines())


def test_default_view(capsys):
    file_path = Path(__file__).parent / 'asset' / 'si-example.db'
    db = load(str(file_path))
    db.accept(ToggleOpenView())
    rr = db.q()
    content_orig = "\n".join([fmt(rr, row, 60) for row in rr.rows])
    full_cli.main([str(file_path), 'view'])
    out_err = capsys.readouterr()
    content = TEST_TEMPLATE.format(
        name="Default view",
        content_orig=content_orig,
        args="",
        status="passes",
        stdout=format_quote(out_err.out),
        stderr=format_quote(out_err.err),
    )
    verify_file(content, ".md")