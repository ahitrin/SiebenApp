# coding: utf-8
from hypothesis import given, note, assume, example
from hypothesis.strategies import integers, lists, sampled_from, composite, choices, streaming
from siebenapp.goaltree import Goals
from siebenapp.system import run_migrations, save_updates
import sqlite3


USER_ACTIONS = {
    'add': lambda g, x: g.add('a'),
    'delete': lambda g, x: g.delete(),
    'hold_select': lambda g, x: g.hold_select(),
    'insert': lambda g, x: g.insert('i'),
    'rename': lambda g, x: g.rename('r'),
    'select': lambda g, x: g.select(x),
    'toggle_close': lambda g, x: g.toggle_close(),
    'toggle_link': lambda g, x: g.toggle_link(),
}


@composite
def user_actions(draw, min_size=0, skip=[]):
    return draw(lists(sampled_from(k for k in USER_ACTIONS.keys() if k not in skip),
                      min_size=min_size))


def build_from(actions, ints):
    ints_index = 0
    g = Goals('Root')
    for name in actions:
        int_val = 0
        if name == 'select':
            int_val = ints[ints_index]
            ints_index += 1
        USER_ACTIONS[name](g, int_val)
    return g


@given(user_actions(), streaming(integers(0, 9)))
def test_there_is_always_at_least_one_goal(actions, ints):
    g = build_from(actions, ints)
    assert g.all()


@given(user_actions(), streaming(integers(0, 9)))
def test_there_is_always_one_selected_goal(actions, ints):
    g = build_from(actions, ints)
    assert len([1 for k, v in g.all(keys='select').items() if v == 'select']) == 1


@given(user_actions(min_size=15,skip=['rename']),
       user_actions(min_size=1, skip=['select']),
       streaming(integers(0, 9)), choices())
def test_any_goal_may_be_selected(all_actions, non_select_actions, ints, choice):
    g = build_from(all_actions + non_select_actions, ints)
    rnd_goal = choice(list(g.all().keys()))
    for i in str(rnd_goal):
        g.select(int(i))
    assert g.all(keys='select')[rnd_goal] == 'select'


@given(user_actions(skip=['rename']), streaming(integers(0, 9)))
def test_all_goals_must_be_connected_to_the_root(actions, ints):
    g = build_from(actions, ints)
    edges = g.all(keys='edge')
    queue, visited = [k for k, v in g.all().items() if v == 'Root'], set()
    while queue:
        goal = queue.pop()
        queue.extend(g for g in edges[goal] if g not in visited)
        visited.add(goal)
    assert visited == set(edges.keys())


@given(user_actions(skip=['rename']), streaming(integers(0, 9)))
def test_all_open_goals_must_be_connected_to_the_root_via_other_open_goals(actions, ints):
    g = build_from(actions, ints)
    open_goals = set(k for k, v in g.all(keys='open').items() if v)
    edges = {k: v for k, v in g.all(keys='edge').items() if k in open_goals}
    assume(edges)
    queue, visited = [k for k, v in g.all().items() if v == 'Root'], set()
    while queue:
        goal = queue.pop()
        queue.extend(g for g in edges[goal] if g not in visited and g in open_goals)
        visited.add(goal)
    assert visited == set(edges.keys())


@given(user_actions(), streaming(integers(0, 9)))
def test_full_export_and_streaming_export_must_be_the_same(actions, ints):
    g = build_from(actions, ints)
    conn = sqlite3.connect(':memory:')
    run_migrations(conn)
    save_updates(g, conn)
    cur = conn.cursor()
    goals = [row for row in cur.execute('select * from goals')]
    edges = [row for row in cur.execute('select * from edges')]
    selection = [row for row in cur.execute('select * from selection')]
    ng = Goals.build(goals, edges, selection)
    assert g.all('name,open,edge,select') == \
            ng.all('name,open,edge,select')
