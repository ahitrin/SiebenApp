# coding: utf-8
from contextlib import closing

import pytest
import sqlite3

from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals
from siebenapp.system import MIGRATIONS, run_migrations, load, save
from tempfile import NamedTemporaryFile

from siebenapp.zoom import Zoom


def test_initial_migration_on_empty_db():
    with closing(sqlite3.connect(':memory:')) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn, MIGRATIONS[:1])
            cur.execute('select version from migrations')
            version = cur.fetchone()[0]
            assert version == 0


def test_skip_passed_migrations():
    with closing(sqlite3.connect(':memory:')) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn, MIGRATIONS[:1])
            run_migrations(conn, MIGRATIONS[:1])
            cur.execute('select version from migrations')
            version = cur.fetchone()[0]
            assert version == 0


def test_last_known_migration():
    with closing(sqlite3.connect(':memory:')) as conn:
        with closing(conn.cursor()) as cur:
            run_migrations(conn)
            cur.execute('select version from migrations')
            version = cur.fetchone()[0]
            assert version == 3


def setup_sample_db(conn):
    with closing(conn.cursor()) as cur:
        sample_goals = [(1, 'Root', True), (2, 'A', True), (3, 'B', False)]
        cur.executemany('insert into goals values (?,?,?)', sample_goals)
        sample_edges = [(1, 2), (1, 3), (2, 3)]
        cur.executemany('insert into edges values (?,?)', sample_edges)
        sample_selects = [('selection', 2), ('previous_selection', 1)]
        cur.executemany('insert into settings values (?,?)', sample_selects)
        conn.commit()


def test_restore_goals_from_db():
    file_name = NamedTemporaryFile().name
    with sqlite3.connect(file_name) as conn:
        run_migrations(conn)
        setup_sample_db(conn)
    actual_goals = load(file_name).goaltree
    expected_goals = Goals('Root')
    expected_goals.add('A')
    expected_goals.add('B')
    expected_goals.select(2)
    expected_goals.hold_select()
    expected_goals.select(3)
    expected_goals.toggle_link()
    expected_goals.select(3)
    expected_goals.toggle_close()
    expected_goals.select(2)
    assert expected_goals.all(keys='name,edge,open,select') == \
            actual_goals.all(keys='name,edge,open,select')
    assert not actual_goals.events


def test_load_from_missing_file():
    file_name = NamedTemporaryFile().name
    expected_goals = Goals('Rename me')
    new_goals = load(file_name)
    assert new_goals.all(keys='open,name,edge,select') == \
            expected_goals.all(keys='open,name,edge,select')


def test_save_into_sqlite3_database():
    file_name = NamedTemporaryFile().name
    goals = Goals('Sample')
    save(goals, file_name)
    with sqlite3.connect(file_name) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute('select version from migrations')
            assert cur.fetchone()[0] > 0


def test_migration_must_run_on_load_from_existing_db():
    file_name = NamedTemporaryFile().name
    goals = Goals('Just a simple goal tree')
    save(goals, file_name)
    MIGRATIONS.append([
        'create table dummy (answer integer)',
        'insert into dummy values (42)',
    ])
    try:
        load(file_name)
        with closing(sqlite3.connect(file_name)) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('select answer from dummy')
                value = cur.fetchone()[0]
                assert value == 42
    finally:
        MIGRATIONS.pop(-1)


def test_save_and_load():
    file_name = NamedTemporaryFile().name
    goals = Enumeration(Zoom(Goals('Root')))
    goals.add('Top')
    goals.add('Middle')
    goals.select(3)
    goals.hold_select()
    goals.select(2)
    goals.toggle_link()
    goals.add('Closed')
    goals.select(4)
    goals.toggle_close()
    goals.select(2)
    goals.toggle_zoom()
    save(goals, file_name)
    new_goals = load(file_name)
    goals.next_view()
    goals.next_view()
    new_goals.next_view()
    new_goals.next_view()
    assert goals.all(keys='open,name,edge,select,top') == \
           new_goals.all(keys='open,name,edge,select,top')


def test_multiple_saves_works_fine():
    file_name = NamedTemporaryFile().name
    goals = Goals('Root')
    save(goals, file_name)
    goals.add('Next')
    save(goals, file_name)
    new_goals = load(file_name)
    assert goals.all() == new_goals.all()


def test_do_not_load_from_broken_data():
    file_name = NamedTemporaryFile().name
    with sqlite3.connect(file_name) as conn:
        run_migrations(conn)
        setup_sample_db(conn)
        with closing(conn.cursor()) as cur:
            cur.execute('delete from goals where goal_id = 2')
    with pytest.raises(AssertionError):
        load(file_name)
