# coding: utf-8
import pickle

DEFAULT_DB = 'sieben.db'


def save(obj, filename=DEFAULT_DB):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load(filename=DEFAULT_DB):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def dot_export(goals):
    data = goals.all(keys='open,name,edge,select')
    tops = goals.top()
    lines = []
    for num in sorted(data.keys()):
        name = '%d: %s' % (num, data[num]['name'])
        color = 'red' if data[num]['open'] else 'green'
        style = ', style=bold' if num in tops else ''
        style = ', style=filled' if data[num]['select'] else style
        fillcolor = ', fillcolor=lightgray' if data[num]['select'] else ''
        lines.append('%d [label="%s", color=%s%s%s];' % (num, name, color, style, fillcolor))
    for num in sorted(data.keys()):
        for edge in data[num]['edge']:
            color = 'black' if data[edge]['open'] else 'grey'
            lines.append('%d -> %d [color=%s];' % (edge, num, color))
    return 'digraph g {\nnode [shape=box];\n%s\n}' % '\n'.join(lines)
