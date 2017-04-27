# coding: utf-8
import sqlite3
from os import path, remove
from siebenapp.goaltree import Goals, Enumeration

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
]


def save(goals, filename=DEFAULT_DB):
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        save_updates(goals, connection)
        connection.close()
    else:
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        goals_export, edges_export, select_export = Goals.export(goals)
        cur = connection.cursor()
        cur.executemany('insert into goals values (?,?,?)', goals_export)
        cur.executemany('insert into edges values (?,?)', edges_export)
        cur.executemany('insert into selection values (?,?)', select_export)
        goals.events.clear()
        connection.commit()
        connection.close()


def save_updates(goals, connection):
    actions = {
        'add': ['insert into goals values (?,?,?)'],
        'toggle_close': ['update goals set open=? where goal_id=?'],
        'rename': ['update goals set name=? where goal_id=?'],
        'link': ['insert into edges values (?,?)'],
        'unlink': ['delete from edges where parent=? and child=?'],
        'select': ['delete from selection where name="selection"',
                   'insert into selection values ("selection", ?)'],
        'hold_select': ['delete from selection where name="previous_selection"',
                        'insert into selection values ("previous_selection", ?)'],
        'delete': ['delete from goals where goal_id=?',
                   'delete from edges where child=?',
                   'delete from edges where parent=?'],
    }
    cur = connection.cursor()
    while len(goals.events) > 0:
        event = goals.events.popleft()
        if event[0] in actions:
            for query in actions[event[0]]:
                if '?' in query:
                    cur.execute(query, event[1:])
                else:
                    cur.execute(query)
    connection.commit()


def load(filename=DEFAULT_DB):
    if not path.isfile(filename):
        return Enumeration(Goals('Rename me'))
    connection = sqlite3.connect(filename)
    cur = connection.cursor()
    goals = [row for row in cur.execute('select * from goals')]
    edges = [row for row in cur.execute('select * from edges')]
    selection = [row for row in cur.execute('select * from selection')]
    cur.close()
    return Enumeration(Goals.build(goals, edges, selection))


def run_migrations(conn, migrations=MIGRATIONS):
    cur = conn.cursor()
    try:
        cur.execute('select version from migrations')
        current_version = cur.fetchone()[0]
    except sqlite3.OperationalError:
        current_version = -1
    for num, migration in enumerate(migrations[current_version + 1:]):
        for query in migration:
            cur.execute(query)
        cur.execute('update migrations set version=?', (num,))
        conn.commit()


def dot_export(goals, view):
    data = goals.all(keys='open,name,edge,select')
    tops = goals.top()
    lines = []
    for num in sorted(data.keys()):
        goal = data[num]
        if view == 'open' and not goal['open']:
            continue
        if view == 'top' and num not in tops:
            continue
        style = []
        if num in tops:
            style.append('bold')
        attributes = {
            'label': '"%d: %s"' % (num, goal['name']),
            'color': 'red' if goal['open'] else 'green',
            'fillcolor': {'select': 'gray', 'prev': 'lightgray'}.get(goal['select']),
        }
        if goal['select'] is not None:
            style.append('filled')
        if len(style) > 1:
            attributes['style'] = '"%s"' % ','.join(style)
        elif len(style) == 1:
            attributes['style'] = style[0]
        attributes_str = ', '.join(
            '%s=%s' % (k, attributes[k])
            for k in ['label', 'color', 'style', 'fillcolor']
            if k in attributes and attributes[k]
        )
        lines.append('%d [%s];' % (num, attributes_str))
    for num in sorted(data.keys()):
        for edge in data[num]['edge']:
            if view == 'top':
                continue
            if view == 'open' and not data[edge]['open']:
                continue
            color = 'black' if data[edge]['open'] else 'gray'
            lines.append('%d -> %d [color=%s];' % (edge, num, color))
    return 'digraph g {\nnode [shape=box];\n%s\n}' % '\n'.join(lines)
