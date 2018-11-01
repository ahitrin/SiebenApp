# coding: utf-8
import sqlite3
from html import escape
from os import path
from typing import Union, Callable, List, Dict

from siebenapp.goaltree import Goals
from siebenapp.enumeration import Enumeration
from siebenapp.zoom import Zoom

DEFAULT_DB = 'sieben.db'
MIGRATIONS = [
    # 0
    [
        'create table migrations (version integer)',
        'insert into migrations values (-1)'
    ],
    # 1
    [
        '''create table goals (
            goal_id integer primary key,
            name string,
            open boolean
        )''',
        '''create table edges (
            parent integer,
            child integer,
            foreign key(parent) references goals(goal_id),
            foreign key(child) references goals(goal_id)
        )''',
        '''create table selection (
            name string,
            goal integer,
            foreign key(goal) references goals(goal_id)
        )'''
    ],
    # 2
    [
        # change type of goals.name: string -> text
        '''alter table goals rename to old_goals''',
        '''create table goals (
            goal_id integer primary key,
            name text,
            open boolean
        )''',
        '''insert into goals (goal_id, name, open)
           select goal_id, name, open from old_goals''',
        '''drop table old_goals''',
        # change type of selection.name: string -> text
        '''alter table selection rename to old_selection''',
        '''create table selection (
            name text,
            goal integer,
            foreign key(goal) references goals(goal_id)
        )''',
        '''insert into selection (name, goal)
           select name, goal from old_selection''',
        '''drop table old_selection''',
    ],
    # 3
    [
        'alter table selection rename to settings',
    ],
    # 4
    [
        'alter table edges add column reltype integer not null default 1'
    ],
    # 5
    [
        '''create table zoom (
            level integer primary key,
            goal integer,
            foreign key(goal) references goals(goal_id)
        )''',
        '''insert into zoom (level, goal) select 1, 1 from settings
           where name = 'zoom' ''',
        '''insert into zoom (level, goal) select 2, goal from settings
           where name = 'zoom' and goal <> 1''',
        "delete from settings where name = 'zoom'",
    ],
]


def save(goals, filename=DEFAULT_DB):
    # type: (Union[Goals, Enumeration, Zoom], str) -> None
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        save_updates(goals, connection)
        connection.close()
    else:
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        goals_export, edges_export, select_export = Goals.export(goals)
        zoom_export = Zoom.export(goals)
        cur = connection.cursor()
        cur.executemany('insert into goals values (?,?,?)', goals_export)
        cur.executemany('insert into edges values (?,?,?)', edges_export)
        cur.executemany('insert into settings values (?,?)', select_export)
        cur.executemany('insert into zoom values (?, ?)', zoom_export)
        goals.events.clear()
        connection.commit()
        connection.close()


def save_updates(goals, connection):
    # type: (Union[Goals, Zoom], sqlite3.Connection) -> None
    actions = {
        'add': ['insert into goals values (?,?,?)'],
        'toggle_close': ['update goals set open=? where goal_id=?'],
        'rename': ['update goals set name=? where goal_id=?'],
        'link': ['insert into edges values (?,?,1)'],
        'unlink': ['delete from edges where parent=? and child=?'],
        'select': ['delete from settings where name="selection"',
                   'insert into settings values ("selection", ?)'],
        'hold_select': ['delete from settings where name="previous_selection"',
                        'insert into settings values ("previous_selection", ?)'],
        'delete': ['delete from goals where goal_id=?',
                   'delete from edges where child=?',
                   'delete from edges where parent=?'],
        'zoom': ['insert into zoom values (?, ?)'],
        'unzoom': ['delete from zoom where goal=?'],
    }
    cur = connection.cursor()
    while goals.events:
        event = goals.events.popleft()
        if event[0] in actions:
            for query in actions[event[0]]:
                if '?' in query:
                    cur.execute(query, event[1:])
                else:
                    cur.execute(query)
    connection.commit()


def load(filename=DEFAULT_DB, message_fn=None):
    # type: (str, Callable[[str], None]) -> Enumeration
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        cur = connection.cursor()
        goals = [row for row in cur.execute('select * from goals')]
        edges = [row for row in cur.execute('select parent, child, reltype from edges')]
        settings = [row for row in cur.execute('select * from settings')]
        zoom_data = [row for row in cur.execute('select * from zoom')]
        cur.close()
        goals = Goals.build(goals, edges, settings, message_fn)
        zoom = Zoom.build(goals, zoom_data)
    else:
        goals = Goals('Rename me', message_fn)
        zoom = Zoom(goals)
    return Enumeration(zoom)


def run_migrations(conn, migrations=None):
    # type: (sqlite3.Connection, List[List[str]]) -> None
    if migrations is None:
        migrations = MIGRATIONS
    cur = conn.cursor()
    try:
        cur.execute('select version from migrations')
        current_version = cur.fetchone()[0]
    except sqlite3.OperationalError:
        current_version = -1
    for num, migration in [(n, m) for n, m in enumerate(migrations)][current_version + 1:]:
        for query in migration:
            cur.execute(query)
        cur.execute('update migrations set version=?', (num,))
        conn.commit()


def split_long(line):
    # type: (str) -> str
    margin = 20
    parts = []
    space_position = line.find(' ', margin)
    while space_position > 0:
        part, line = line[:space_position], line[(space_position + 1):]
        parts.append(part)
        space_position = line.find(' ', margin)
    parts.append(line)
    return '\n'.join(parts)


def _format_name(num, goal):
    # type: (int, Dict[str, str]) -> str
    goal_name = escape(goal['name'])
    label = '"%d: %s"' % (num, goal_name) if num >= 0 else '"%s"' % goal_name
    return split_long(label)
