# coding: utf-8
import pickle
from mikado import Goals

DEFAULT_DB = 'sieben.db'


def save(obj, filename=DEFAULT_DB):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load(filename=DEFAULT_DB):
    with open(filename, 'rb') as f:
        return pickle.load(f)


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


def dot_export(goals):
    data = goals.all(keys='open,name,edge,select')
    tops = goals.top()
    lines = []
    for num in sorted(data.keys()):
        goal = data[num]
        attributes = {
            'label': '"%d: %s"' % (num, goal['name']),
            'color': 'red' if goal['open'] else 'green',
            'fillcolor': 'lightgray' if goal['select'] else None,
            'style': 'bold' if num in tops else None,
        }
        if goal['select']:
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
            color = 'black' if data[edge]['open'] else 'grey'
            lines.append('%d -> %d [color=%s];' % (edge, num, color))
    return 'digraph g {\nnode [shape=box];\n%s\n}' % '\n'.join(lines)
