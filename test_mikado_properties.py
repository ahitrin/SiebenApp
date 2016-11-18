# coding: utf-8
from mikado import Goals
from hypothesis import given, note
from hypothesis.strategies import integers, lists, tuples, sampled_from, composite


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
def user_actions(draw):
    actions = draw(lists(tuples(
        sampled_from(USER_ACTIONS.keys()),
        integers(0, 9)
    )))
    return actions


def pretty_print(actions):
    result = []
    for name, int_val in actions:
        if name == 'select':
            result.append('%s %d' % (name, int_val))
        elif name in ['add', 'insert']:
            result.append('%s foo' % name)
        else:
            result.append(name)
    return result


@given(user_actions())
def test_there_is_always_at_least_one_goal(actions):
    g = Goals('Indeletable')
    note(pretty_print(actions))
    for name, int_val in actions:
        USER_ACTIONS[name](g, int_val)
    assert g.all()
