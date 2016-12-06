# coding: utf-8
import pickle
import sqlite3
from os import path
from siebenapp.goaltree import Goals, build_goals

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


def save(obj, filename=DEFAULT_DB):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load(filename=DEFAULT_DB):
    if not path.isfile(filename):
        return Goals('Rename me')
    try:
        connection = sqlite3.connect(filename)
        cur = connection.cursor()
        goals = [row for row in cur.execute('select * from goals')]
        edges = [row for row in cur.execute('select * from edges')]
        selection = [row for row in cur.execute('select * from selection')]
        cur.close()
        return build_goals(goals, edges, selection)
    except sqlite3.DatabaseError:
        # Temporary fallback to pickle
        with open(filename, 'rb') as f:
            return pickle.load(f)


def run_migrations(conn, migrations=MIGRATIONS):
    cur = conn.cursor()
    try:
        cur.execute('select version from migrations')
        current_version = cur.fetchone()[0]
    except sqlite3.OperationalError:
        current_version = -1
    for num, migration in enumerate(migrations):
        if num <= current_version:
            continue
        for query in migration:
            cur.execute(query)
        cur.execute('update migrations set version=?', (num,))
        conn.commit()


def rescue_db(filename=DEFAULT_DB):
    old_goals = load(filename)
    new_goals = Goals('rescue')
    new_goals.goals = old_goals.goals
    new_goals.edges = old_goals.edges
    new_goals.closed = old_goals.closed
    new_goals.selection = 1
    new_goals.selection_cache = []
    new_goals.previous_selection = 1
    save(new_goals, filename)


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
