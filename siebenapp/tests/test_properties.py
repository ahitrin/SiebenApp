# coding: utf-8
import os
import sqlite3
from contextlib import closing

from hypothesis import given, note, settings, example
from hypothesis._strategies import data, integers
from hypothesis.strategies import lists, sampled_from, composite, choices, text

from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals, Edge
from siebenapp.system import run_migrations, save_updates

settings.register_profile('ci', settings(max_examples=2000))
settings.register_profile('dev', settings(max_examples=200))
settings.load_profile(os.getenv('HYPOTHESIS_PROFILE', 'dev'))


USER_ACTIONS = {
    'add': lambda g, x: g.add('a'),
    'delete': lambda g, x: g.delete(),
    'hold_select': lambda g, x: g.hold_select(),
    'insert': lambda g, x: g.insert('i'),
    'rename': lambda g, x: g.rename('r'),
    'select': lambda g, x: g.select(x),
    'toggle_close': lambda g, x: g.toggle_close(),
    'toggle_link': lambda g, x: g.toggle_link(),
    'toggle_child': lambda g, x: g.toggle_link(edge_type=Edge.PARENT),
}


@composite
def user_actions(draw, skip=None, **lists_kwargs):
    if skip is None:
        skip = []
    possible_actions = sorted(k for k in USER_ACTIONS if k not in skip)
    return draw(lists(sampled_from(possible_actions), **lists_kwargs))


def build_from(actions, selections, show_notes=True):
    def _select_one_from(keys):
        if isinstance(selections, list):
            return selections.pop(0)
        return selections.draw(integers(min_value=1, max_value=max(keys)))

    g = Goals('Root')
    try:
        for name in actions:
            int_val = 0
            if name == 'select':
                int_val = _select_one_from(g.q().keys())
            USER_ACTIONS[name](g, int_val)
    finally:
        if show_notes:
            note(actions)
    return g


@given(user_actions(), data())
@example(actions=['add', 'add', 'select', 'toggle_close', 'select', 'hold_select', 'select', 'toggle_link'],
         selections=[2, 2, 3])
@example(actions=['add', 'select', 'add', 'add', 'select', 'hold_select', 'select', 'insert', 'select', 'delete'],
         selections=[2, 4, 3, 2])
@example(actions=['add', 'select', 'insert', 'toggle_link', 'toggle_close', 'select', 'toggle_close', 'select', 'toggle_close'],
         selections=[2, 3, 2])
@example(actions=['add', 'select', 'hold_select', 'add', 'select', 'insert', 'toggle_link', 'select', 'delete'],
         selections=[2, 3, 2])
def test_goaltree_must_be_valid_after_build(actions, selections):
    g = build_from(actions, selections, show_notes=False)
    assert g.verify()


@given(user_actions(), data())
def test_there_is_always_at_least_one_goal(actions, selections):
    g = build_from(actions, selections)
    assert g.q()


@given(user_actions(), data())
def test_there_is_always_one_selected_goal(actions, selections):
    g = build_from(actions, selections)
    assert len([1 for k, v in g.q(keys='select').items() if v['select'] == 'select']) == 1


@given(user_actions(min_size=15, skip=['rename']),
       user_actions(min_size=1, skip=['select']),
       data(), choices())
def test_any_goal_may_be_selected(all_actions, non_select_actions, selections, choice):
    g = build_from(all_actions + non_select_actions, selections)
    rnd_goal = choice(list(g.q().keys()))
    g.select(rnd_goal)
    assert g.q(keys='select')[rnd_goal]['select'] == 'select'


@given(user_actions(skip=['rename']), data(), choices())
def test_any_goal_may_be_selected_through_enumeration(actions, selections, choice):
    g = build_from(actions, selections)
    e = Enumeration(g)
    e.next_view()
    e.next_view()
    rnd_goal = choice(list(e.q().keys()))
    for i in str(rnd_goal):
        e.select(int(i))
    assert e.q(keys='select')[rnd_goal]['select'] == 'select'


@given(user_actions(), data())
def test_no_modify_action_sequence_could_break_goaltree_correctness(actions, selections):
    g = build_from(actions, selections)
    assert g.verify()


def build_goals(conn):
    with closing(conn.cursor()) as cur:
        goals = [row for row in cur.execute('select * from goals')]
        edges = [row for row in cur.execute('select parent, child, reltype from edges')]
        selection = [row for row in cur.execute('select * from settings')]
        note(goals)
        note(edges)
        note(selection)
        return Goals.build(goals, edges, selection)


@given(user_actions(), data())
def test_full_export_and_streaming_export_must_be_the_same(actions, selections):
    g = build_from(actions, selections)
    with closing(sqlite3.connect(':memory:')) as conn:
        run_migrations(conn)
        note(g.events)
        save_updates(g, conn)
        assert not g.events
        ng = build_goals(conn)
        assert g.q('name,open,edge,select') == ng.q('name,open,edge,select')


@given(text())
def test_all_goal_names_must_be_saved_correctly(name):
    g = Goals('renamed')
    g.rename(name)
    with closing(sqlite3.connect(':memory:')) as conn:
        note(g.events)
        run_migrations(conn)
        save_updates(g, conn)
        ng = build_goals(conn)
        assert g.q('name,open,edge,select') == ng.q('name,open,edge,select')


def test_all_keys_in_enumeration_must_be_of_the_same_length():
    g = Goals('Root')
    for i in range(2999):
        g.add(str(i))
    e = Enumeration(g)
    mapping = e.q()
    assert len(mapping) == len(g.q())
    assert set(len(str(k)) for k in mapping) == {4}
