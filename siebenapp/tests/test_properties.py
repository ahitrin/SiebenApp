# coding: utf-8
import os
from contextlib import closing

from hypothesis import given, note, settings
from hypothesis.strategies import lists, sampled_from, composite, choices, text
from siebenapp.goaltree import Goals
from siebenapp.enumeration import Enumeration
from siebenapp.system import run_migrations, save_updates
import pytest
import sqlite3


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
}


@composite
def user_actions(draw, skip=list(), **lists_kwargs):
    return draw(lists(sampled_from(k for k in USER_ACTIONS.keys() if k not in skip),
                      **lists_kwargs))


def build_from(actions, choice_fn, show_notes=True):
    g = Goals('Root')
    try:
        for name in actions:
            int_val = 0
            if name == 'select':
                int_val = choice_fn(list(g.all().keys()))
            USER_ACTIONS[name](g, int_val)
    finally:
        if show_notes:
            note(actions)
    return g


@pytest.mark.parametrize('actions,ints', [
    (['add', 'add', 'select', 'toggle_close', 'select', 'hold_select', 'select', 'toggle_link'],
     [2, 2, 3]),
    (['add', 'select', 'add', 'add', 'select', 'hold_select', 'select', 'insert', 'select', 'delete'],
     [2, 4, 3, 2]),
    (['add', 'select', 'insert', 'toggle_link', 'toggle_close', 'select', 'toggle_close', 'select', 'toggle_close'],
     [2, 3, 2]),
    (['add', 'select', 'hold_select', 'add', 'select', 'insert', 'toggle_link', 'select', 'delete'],
     [2, 3, 2]),
])
def test_bad_examples_found_by_hypothesis(actions, ints):
    def repeat_choices(l):
        def inner(gs):
            assert l, 'There are no more selects expected'
            next_result = l.pop(0)
            assert next_result in gs, 'Goal with id %d should be selected, but existing goals are %s' % (
                next_result, gs
            )
            return next_result
        return inner
    g = build_from(actions, repeat_choices(ints), show_notes=False)
    assert g.verify()


@given(user_actions(), choices())
def test_there_is_always_at_least_one_goal(actions, ch):
    g = build_from(actions, ch)
    assert g.all()


@given(user_actions(), choices())
def test_there_is_always_one_selected_goal(actions, ch):
    g = build_from(actions, ch)
    assert len([1 for k, v in g.all(keys='select').items() if v['select'] == 'select']) == 1


@given(user_actions(min_size=15, skip=['rename']),
       user_actions(min_size=1, skip=['select']),
       choices(), choices())
def test_any_goal_may_be_selected(all_actions, non_select_actions, ch, choice):
    g = build_from(all_actions + non_select_actions, ch)
    rnd_goal = choice(list(g.all().keys()))
    g.select(rnd_goal)
    assert g.all(keys='select')[rnd_goal]['select'] == 'select'


@given(user_actions(average_size=100, skip=['rename']), choices(), choices())
def test_any_goal_may_be_selected_through_enumeration(actions, ch, choice):
    g = build_from(actions, ch)
    e = Enumeration(g)
    e.next_view()
    e.next_view()
    rnd_goal = choice(list(e.all().keys()))
    for i in str(rnd_goal):
        e.select(int(i))
    assert e.all(keys='select')[rnd_goal]['select'] == 'select'


@given(user_actions(average_size=100), choices())
def test_no_modify_action_sequence_could_break_goaltree_correctness(actions, ch):
    g = build_from(actions, ch)
    assert g.verify()


def build_goals(conn):
    with closing(conn.cursor()) as cur:
        goals = [row for row in cur.execute('select * from goals')]
        edges = [row for row in cur.execute('select * from edges')]
        selection = [row for row in cur.execute('select * from settings')]
        note(goals)
        note(edges)
        note(selection)
        return Goals.build(goals, edges, selection)


@given(user_actions(), choices())
def test_full_export_and_streaming_export_must_be_the_same(actions, ch):
    g = build_from(actions, ch)
    with closing(sqlite3.connect(':memory:')) as conn:
        run_migrations(conn)
        note(g.events)
        save_updates(g, conn)
        assert not g.events
        ng = build_goals(conn)
        assert g.all('name,open,edge,select') == ng.all('name,open,edge,select')


@given(text())
def test_all_goal_names_must_be_saved_correctly(name):
    g = Goals('renamed')
    g.rename(name)
    with closing(sqlite3.connect(':memory:')) as conn:
        note(g.events)
        run_migrations(conn)
        save_updates(g, conn)
        ng = build_goals(conn)
        assert g.all('name,open,edge,select') == ng.all('name,open,edge,select')


def test_all_keys_in_enumeration_must_be_of_the_same_length():
    g = Goals('Root')
    for i in range(2999):
        g.add(str(i))
    e = Enumeration(g)
    mapping = e.all()
    assert len(mapping) == len(g.all())
    assert set(len(str(k)) for k in mapping) == {4}
