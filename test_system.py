# coding: utf-8
from mikado import Goals
from system import save, load, dot_export
from tempfile import NamedTemporaryFile


def test_save_and_load():
    file_name = NamedTemporaryFile().name
    goals = Goals('Root')
    goals.add('Top')
    goals.add('Middle')
    goals.link(3, 2)
    goals.add('Closed')
    goals.close(4)
    save(goals, file_name)
    new_goals = load(file_name)
    assert goals.all(keys='open,name,edge') == new_goals.all(keys='open,name,edge')


def test_dot_export_with_closed():
    g = Goals('Root')
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.close(4)
    assert dot_export(g) == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red, style=filled, fillcolor=lightgray];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style=bold];
4 [label="4: Closed", color=green];
2 -> 1 [color=black];
4 -> 1 [color=grey];
3 -> 2 [color=black];
}'''
    g.select(3)
    assert dot_export(g) == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style="bold,filled", fillcolor=lightgray];
4 [label="4: Closed", color=green];
2 -> 1 [color=black];
4 -> 1 [color=grey];
3 -> 2 [color=black];
}'''
