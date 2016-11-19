# coding: utf-8
from mikado import Goals
from hypothesis import given, note, assume
from hypothesis.strategies import integers, lists, tuples, sampled_from, composite, randoms


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
    g = Goals('Root')
    note(pretty_print(actions))
    for name, int_val in actions:
        USER_ACTIONS[name](g, int_val)
    assert g.all()


@given(user_actions(), randoms())
def test_any_goal_may_be_selected(actions, rnd):
    # skip actions having 'select' at the end
    assume(actions[-1][0] != 'select' if actions else True)
    note(pretty_print(actions))
    g = Goals('Root')
    for name, int_val in actions:
        USER_ACTIONS[name](g, int_val)
    rnd_goal = rnd.sample(g.all().keys(), 1)[0]
    note('Select: %d' % rnd_goal)
    for i in str(rnd_goal):
        g.select(int(i))
    assert g.all(keys='select')[rnd_goal] == True
