# coding: utf-8
from siebenapp.goaltree import Goals, Enumeration
from siebenapp.system import dot_export


def test_dot_export_full_view():
    g = Enumeration(Goals('Root'))
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    g.next_view()
    g.next_view()
    assert dot_export(g) == '''digraph g {
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
    assert dot_export(g) == '''digraph g {
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
    g = Enumeration(Goals('Root'))
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    assert dot_export(g) == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red, style=filled, fillcolor=gray];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style=bold];
2 -> 1 [color=black];
3 -> 2 [color=black];
}'''


def test_dot_export_top_view():
    g = Enumeration(Goals('Root'))
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    g.next_view()
    assert dot_export(g) == '''digraph g {
node [shape=box];
3 [label="3: Top", color=red, style=bold];
}'''
