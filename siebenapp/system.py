# coding: utf-8
import sqlite3
from os import path, remove
from siebenapp.goaltree import Goals

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
]


def save(goals, filename=DEFAULT_DB):
    if path.isfile(filename):
        remove(filename)
    connection = sqlite3.connect(filename)
    run_migrations(connection)
    goals_export, edges_export, select_export = Goals.export(goals)
    cur = connection.cursor()
    cur.executemany('insert into goals values (?,?,?)', goals_export)
    cur.executemany('insert into edges values (?,?)', edges_export)
    cur.executemany('insert into selection values (?,?)', select_export)
    connection.commit()
    connection.close()


def save_updates(goals, connection):
    cur = connection.cursor()
    for event in goals.events:
        if event[0] == 'add':
            cur.execute('insert into goals values (?,?,?)', event[1:])
        elif event[0] == 'toggle_close':
            cur.execute('update goals set open=? where goal_id=?', event[1:])
        elif event[0] == 'rename':
            cur.execute('update goals set name=? where goal_id=?', event[1:])
        elif event[0] == 'link':
            cur.execute('insert into edges values (?,?)', event[1:])
        elif event[0] == 'unlink':
            cur.execute('delete from edges where parent=? and child=?', event[1:])
        elif event[0] == 'select':
            cur.execute('delete from selection where name="selection"')
            cur.execute('insert into selection values ("selection", ?)', event[1:])
        elif event[0] == 'hold_select':
            cur.execute('delete from selection where name="previous_selection"')
            cur.execute('insert into selection values ("previous_selection", ?)', event[1:])
        elif event[0] == 'delete':
            cur.execute('delete from goals where goal_id=?', event[1:])
            cur.execute('delete from edges where child=?', event[1:])
            cur.execute('delete from edges where parent=?', event[1:])
    connection.commit()


def load(filename=DEFAULT_DB):
    if not path.isfile(filename):
        return Goals('Rename me')
    connection = sqlite3.connect(filename)
    cur = connection.cursor()
    goals = [row for row in cur.execute('select * from goals')]
    edges = [row for row in cur.execute('select * from edges')]
    selection = [row for row in cur.execute('select * from selection')]
    cur.close()
    return Goals.build(goals, edges, selection)


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
        attributes = {
            'label': '"%d: %s"' % (num, goal['name']),
            'color': 'red' if goal['open'] else 'green',
            'fillcolor': {'select': 'gray', 'prev': 'lightgray'}.get(goal['select']),
            'style': 'bold' if num in tops else None,
        }
        if goal['select'] is not None:
            if attributes['style']:
                attributes['style'] = '"%s,filled"' % attributes['style']
            else:
                attributes['style'] = 'filled'
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
