# coding: utf-8
from goaltree import Goals
from system import save, load, dot_export
from tempfile import NamedTemporaryFile


def test_save_and_load():
    file_name = NamedTemporaryFile().name
    goals = Goals('Root')
    goals.add('Top')
    goals.add('Middle')
    goals.select(3)
    goals.hold_select()
    goals.select(2)
    goals.toggle_link()
    goals.add('Closed')
    goals.select(4)
    goals.toggle_close()
    save(goals, file_name)
    new_goals = load(file_name)
    assert goals.all(keys='open,name,edge,select') == new_goals.all(keys='open,name,edge,select')


def test_dot_export_full_view():
    g = Goals('Root')
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    assert dot_export(g, 'full') == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red, style=filled, fillcolor=gray];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style=bold];
4 [label="4: Closed", color=green];
2 -> 1 [color=black];
4 -> 1 [color=gray];
3 -> 2 [color=black];
}'''
    g.select(3)
    assert dot_export(g, 'full') == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red, style=filled, fillcolor=lightgray];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style="bold,filled", fillcolor=gray];
4 [label="4: Closed", color=green];
2 -> 1 [color=black];
4 -> 1 [color=gray];
3 -> 2 [color=black];
}'''

def test_dot_export_open_view():
    g = Goals('Root')
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    assert dot_export(g, 'open') == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red, style=filled, fillcolor=gray];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style=bold];
2 -> 1 [color=black];
3 -> 2 [color=black];
}'''

def test_dot_export_top_view():
    g = Goals('Root')
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    assert dot_export(g, 'top') == '''digraph g {
node [shape=box];
3 [label="3: Top", color=red, style=bold];
}'''
