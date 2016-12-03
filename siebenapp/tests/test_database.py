# coding: utf-8
import sqlite3


def test_initial_migration():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    cur.execute('create table migrations (version integer)')
    cur.execute('insert into migrations values (0)')
    conn.commit()
    cur.execute('select version from migrations')
    version = cur.fetchone()[0]
    assert version == 0


def test_goals_table():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    cur.execute('''create table goals (
        goal_id integer primary key,
        name string,
        open boolean
    )''')
    sample_goals = [(1, 'Root', True), (2, 'A', True), (3, 'B', False)]
    cur.executemany('insert into goals values (?,?,?)', sample_goals)
    conn.commit()
    goals = [row for row in cur.execute('select * from goals')]
    assert goals == [
        (1, 'Root', True),
        (2, 'A', True),
        (3, 'B', False),
    ]


def test_edges_table():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    cur.execute('''create table edges (
        parent integer,
        child integer
    )''')
    sample_edges = [(1, 2), (1, 3), (2, 3)]
    cur.executemany('insert into edges values (?,?)', sample_edges)
    conn.commit()
    edges = [row for row in cur.execute('select * from edges')]
    assert edges == [(1, 2), (1, 3), (2, 3)]


def test_selection_table():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    cur.execute('''create table selection (
        name string,
        goal integer
    )''')
    sample_selects = [('selection', 2), ('previous_selection', 1)]
    cur.executemany('insert into selection values (?,?)', sample_selects)
    conn.commit()
    selection = [row for row in cur.execute('select * from selection')]
    assert selection == [
        ('selection', 2),
        ('previous_selection', 1),
    ]
