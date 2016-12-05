# coding: utf-8
import sqlite3
from siebenapp.system import MIGRATIONS, run_migrations


def test_initial_migration_on_empty_db():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    run_migrations(conn, MIGRATIONS[:1])
    cur.execute('select version from migrations')
    version = cur.fetchone()[0]
    assert version == 0


def setup_sample_db(conn):
    cur = conn.cursor()
    sample_goals = [(1, 'Root', True), (2, 'A', True), (3, 'B', False)]
    cur.executemany('insert into goals values (?,?,?)', sample_goals)
    sample_edges = [(1, 2), (1, 3), (2, 3)]
    cur.executemany('insert into edges values (?,?)', sample_edges)
    sample_selects = [('selection', 2), ('previous_selection', 1)]
    cur.executemany('insert into selection values (?,?)', sample_selects)
    conn.commit()
    cur.close()


def test_goals_table():
    conn = sqlite3.connect(':memory:')
    run_migrations(conn)
    setup_sample_db(conn)
    cur = conn.cursor()
    goals = [row for row in cur.execute('select * from goals')]
    assert goals == [
        (1, 'Root', True),
        (2, 'A', True),
        (3, 'B', False),
    ]


def test_edges_table():
    conn = sqlite3.connect(':memory:')
    run_migrations(conn)
    setup_sample_db(conn)
    cur = conn.cursor()
    edges = [row for row in cur.execute('select * from edges')]
    assert edges == [(1, 2), (1, 3), (2, 3)]


def test_selection_table():
    conn = sqlite3.connect(':memory:')
    run_migrations(conn)
    setup_sample_db(conn)
    cur = conn.cursor()
    selection = [row for row in cur.execute('select * from selection')]
    assert selection == [
        ('selection', 2),
        ('previous_selection', 1),
    ]
