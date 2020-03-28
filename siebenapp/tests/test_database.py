# coding: utf-8
import sqlite3

from contextlib import closing
from tempfile import NamedTemporaryFile

import pytest

from siebenapp.domain import (
    HoldSelect,
    ToggleClose,
    ToggleLink,
    Add,
    Select,
    ToggleZoom,
    NextView,
)
from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals
from siebenapp.system import MIGRATIONS, run_migrations, load, save
from siebenapp.zoom import Zoom


def test_initial_migration_on_empty_db():
    with closing(sqlite3.connect(":memory:")) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn, MIGRATIONS[:1])
            cur.execute("select version from migrations")
            version = cur.fetchone()[0]
            assert version == 0


def test_skip_passed_migrations():
    with closing(sqlite3.connect(":memory:")) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn, MIGRATIONS[:1])
            run_migrations(conn, MIGRATIONS[:1])
            cur.execute("select version from migrations")
            version = cur.fetchone()[0]
            assert version == 0


def test_last_known_migration():
    with closing(sqlite3.connect(":memory:")) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn)
            cur.execute("select version from migrations")
            version = cur.fetchone()[0]
            assert version == 6


def setup_sample_db(conn):
    with closing(conn.cursor()) as cur:
        sample_goals = [(1, "Root", True), (2, "A", True), (3, "B", False)]
        cur.executemany("insert into goals values (?,?,?)", sample_goals)
        sample_edges = [(1, 2, 2), (1, 3, 2), (2, 3, 1)]
        cur.executemany("insert into edges values (?,?,?)", sample_edges)
        sample_selects = [("selection", 2), ("previous_selection", 1)]
        cur.executemany("insert into settings values (?,?)", sample_selects)
        conn.commit()


def test_restore_goals_from_db():
    file_name = NamedTemporaryFile().name
    with sqlite3.connect(file_name) as conn:
        run_migrations(conn)
        setup_sample_db(conn)
    actual_goals = load(file_name).goaltree
    expected_goals = Goals("Root")
    expected_goals.accept(Add("A"))
    expected_goals.accept(Add("B"))
    expected_goals.accept(Select(2))
    expected_goals.accept(HoldSelect())
    expected_goals.accept(Select(3))
    expected_goals.accept(ToggleLink())
    expected_goals.accept(Select(3))
    expected_goals.accept(ToggleClose())
    expected_goals.accept(Select(2))
    assert expected_goals.q(keys="name,edge,open,select") == actual_goals.q(
        keys="name,edge,open,select"
    )
    assert not actual_goals.events


def test_load_from_missing_file():
    file_name = NamedTemporaryFile().name
    expected_goals = Goals("Rename me")
    new_goals = load(file_name)
    assert new_goals.q(keys="open,name,edge,select") == expected_goals.q(
        keys="open,name,edge,select"
    )


def test_save_into_sqlite3_database():
    file_name = NamedTemporaryFile().name
    goals = Zoom(Goals("Sample"))
    save(goals, file_name)
    with sqlite3.connect(file_name) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute("select version from migrations")
            assert cur.fetchone()[0] > 0


def test_migration_must_run_on_load_from_existing_db():
    file_name = NamedTemporaryFile().name
    goals = Zoom(Goals("Just a simple goal tree"))
    save(goals, file_name)
    MIGRATIONS.append(
        ["create table dummy (answer integer)", "insert into dummy values (42)",]
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


def test_save_and_load():
    file_name = NamedTemporaryFile().name
    goals = Enumeration(Zoom(Goals("Root")))
    goals.accept(Add("Top"))
    goals.accept(Add("Middle"))
    goals.accept(Select(3))
    goals.accept(HoldSelect())
    goals.accept(Select(2))
    goals.accept(ToggleLink())
    goals.accept(Add("Closed"))
    goals.accept(Select(4))
    goals.accept(ToggleClose())
    goals.accept(Select(2))
    goals.accept(ToggleZoom())
    save(goals, file_name)
    new_goals = load(file_name)
    goals.accept(NextView())
    goals.accept(NextView())
    new_goals.accept(NextView())
    new_goals.accept(NextView())
    assert goals.q(keys="open,name,edge,select,switchable") == new_goals.q(
        keys="open,name,edge,select,switchable"
    )


def test_multiple_saves_works_fine():
    file_name = NamedTemporaryFile().name
    goals = Zoom(Goals("Root"))
    save(goals, file_name)
    goals.accept(Add("Next"))
    save(goals, file_name)
    new_goals = load(file_name)
    assert goals.q() == new_goals.q()


def test_do_not_load_from_broken_data():
    file_name = NamedTemporaryFile().name
    with sqlite3.connect(file_name) as conn:
        run_migrations(conn)
        setup_sample_db(conn)
        with closing(conn.cursor()) as cur:
            cur.execute("delete from goals where goal_id = 2")
    with pytest.raises(AssertionError):
        load(file_name)
