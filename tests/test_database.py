import sqlite3
from contextlib import closing
from tempfile import NamedTemporaryFile

import pytest

from siebenapp.domain import (
    ToggleClose,
    ToggleLink,
    Add,
    EdgeType,
)
from siebenapp.selectable import Select, HoldSelect
from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals
from siebenapp.layers import all_layers
from siebenapp.open_view import ToggleOpenView
from siebenapp.system import MIGRATIONS, run_migrations, load, save
from siebenapp.zoom import ToggleZoom


def test_initial_migration_on_empty_db() -> None:
    with closing(sqlite3.connect(":memory:")) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn, MIGRATIONS[:1])
            cur.execute("select version from migrations")
            version = cur.fetchone()[0]
            assert version == 0


def test_skip_passed_migrations() -> None:
    with closing(sqlite3.connect(":memory:")) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn, MIGRATIONS[:1])
            run_migrations(conn, MIGRATIONS[:1])
            cur.execute("select version from migrations")
            version = cur.fetchone()[0]
            assert version == 0


def test_last_known_migration() -> None:
    with closing(sqlite3.connect(":memory:")) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn)
            cur.execute("select version from migrations")
            version = cur.fetchone()[0]
            assert version == 8


def setup_sample_db(conn):
    with closing(conn.cursor()) as cur:
        sample_goals = [(1, "Root", True), (2, "A", True), (3, "B", False)]
        cur.executemany("insert into goals values (?,?,?)", sample_goals)
        sample_edges = [
            (1, 2, EdgeType.PARENT),
            (1, 3, EdgeType.PARENT),
            (2, 3, EdgeType.BLOCKER),
        ]
        cur.executemany("insert into edges values (?,?,?)", sample_edges)
        sample_selects = [("selection", 2), ("previous_selection", 1)]
        cur.executemany("insert into settings values (?,?)", sample_selects)
        conn.commit()


def test_restore_goals_from_db() -> None:
    file_name = NamedTemporaryFile().name
    with sqlite3.connect(file_name) as conn:
        run_migrations(conn)
        setup_sample_db(conn)
    actual_goals = load(file_name)
    actual_goals.accept(ToggleOpenView())
    expected_goals = Enumeration(all_layers(Goals("Root")))
    expected_goals.accept_all(
        Add("A", 1),
        Add("B", 1),
        Select(2),
        HoldSelect(),
        Select(3),
        ToggleLink(2, 3),
        Select(3),
        ToggleClose(3),
        Select(1),
        HoldSelect(),
        Select(2),
        ToggleOpenView(),
    )
    assert expected_goals.q() == actual_goals.q()
    assert not actual_goals.events()


def test_load_from_missing_file() -> None:
    file_name = NamedTemporaryFile().name
    expected_goals = Enumeration(all_layers(Goals("Rename me")))
    new_goals = load(file_name)
    assert new_goals.q() == expected_goals.q()


def test_save_into_sqlite3_database() -> None:
    file_name = NamedTemporaryFile().name
    goals = all_layers(Goals("Sample"))
    save(goals, file_name)
    with sqlite3.connect(file_name) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute("select version from migrations")
            assert cur.fetchone()[0] > 0


def test_migration_must_run_on_load_from_existing_db() -> None:
    file_name = NamedTemporaryFile().name
    goals = all_layers(Goals("Just a simple goal tree"))
    save(goals, file_name)
    MIGRATIONS.append(
        [
            "create table dummy (answer integer)",
            "insert into dummy values (42)",
        ]
    )
    try:
        load(file_name)
        with closing(sqlite3.connect(file_name)) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("select answer from dummy")
                value = cur.fetchone()[0]
                assert value == 42
    finally:
        MIGRATIONS.pop(-1)


def test_save_and_load() -> None:
    file_name = NamedTemporaryFile().name
    goals = Enumeration(all_layers(Goals("Root")))
    goals.accept_all(
        Add("Top", 1),
        Add("Middle", 1),
        Select(3),
        HoldSelect(),
        Select(2),
        ToggleLink(3, 2),
        Add("Closed", 2),
        Select(4),
        ToggleClose(4),
        Select(2),
        ToggleZoom(2),
    )
    save(goals, file_name)
    new_goals = load(file_name)
    goals.accept_all(ToggleOpenView())
    new_goals.accept_all(ToggleOpenView())
    assert goals.q() == new_goals.q()


def test_multiple_saves_works_fine() -> None:
    file_name = NamedTemporaryFile().name
    goals = all_layers(Goals("Root"))
    save(goals, file_name)
    goals.accept(Add("Next", 1))
    save(goals, file_name)
    new_goals = load(file_name)
    assert goals.q() == new_goals.q()


def test_do_not_load_from_broken_data() -> None:
    file_name = NamedTemporaryFile().name
    with sqlite3.connect(file_name) as conn:
        run_migrations(conn)
        setup_sample_db(conn)
        with closing(conn.cursor()) as cur:
            cur.execute("delete from goals where goal_id = 2")
    with pytest.raises(AssertionError):
        load(file_name)
