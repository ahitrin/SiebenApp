# coding: utf-8
from siebenapp.goaltree import Goals
from siebenapp.enumeration import Enumeration
from siebenapp.system import dot_export
from siebenapp.zoom import Zoom


def test_dot_export_full_view():
    g = Enumeration(Goals('Root'))
    g.add('Middle')
    g.add('Top', 2)
    g.add('Closed')
    g.select(4)
    g.toggle_close()
    g.next_view()
    g.next_view()
    g.select(1)
    assert dot_export(g) == '''digraph g {
node [shape=box];
1 [label="1: Root", color=red, style=filled, fillcolor=gray];
2 [label="2: Middle", color=red];
3 [label="3: Top", color=red, style="bold,filled", fillcolor=lightgray];
4 [label="4: Closed", color=green];
2 -> 1 [color=black];
4 -> 1 [color=gray];
3 -> 2 [color=black];
}'''
    g.hold_select()
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
    g.add('More closed', 3)
    # close 'More closed'
    g.select(5)
    g.toggle_close()
    # close 'Closed'
    g.select(4)
    g.toggle_close()
    g.next_view()
    assert dot_export(g) == '''digraph g {
node [shape=box];
1 [label="1: Top", color=red, style="bold,filled", fillcolor=gray];
}'''


def test_dot_export_zoomed_goal_tree():
    g = Enumeration(Zoom(Goals('Root goal')))
    g.add('Hidden intermediate')
    g.add('Zoom root', 2)
    g.add('Hidden neighbour', 2)
    g.add('Visible top', 3)
    g.toggle_link(4, 5)
    g.select(3)
    g.toggle_zoom()
    assert dot_export(g) == '''digraph g {
node [shape=box];
-1 [label="Root goal", color=red];
1 [label="1: Zoom root", color=red, style=filled, fillcolor=gray];
2 [label="2: Visible top", color=red, style=bold];
1 -> -1 [color=black, style=dashed];
2 -> 1 [color=black];
}'''