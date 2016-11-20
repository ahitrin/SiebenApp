# coding: utf-8
from mikado import Goals
from hypothesis import given, note, assume
from hypothesis.strategies import integers, lists, tuples, sampled_from, composite, choices


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
    actions = draw(lists(tuples(
        sampled_from(k for k in USER_ACTIONS.keys() if k not in skip),
        integers(0, 9)
    ), min_size=min_size))
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


@given(user_actions(), user_actions(min_size=1, skip=['select']), choices())
def test_any_goal_may_be_selected(all_actions, non_select_actions, choice):
    note(pretty_print(all_actions))
    note(pretty_print(non_select_actions))
    g = Goals('Root')
    for name, int_val in all_actions + non_select_actions:
        USER_ACTIONS[name](g, int_val)
    rnd_goal = choice(list(g.all().keys()))
    for i in str(rnd_goal):
        g.select(int(i))
    assert g.all(keys='select')[rnd_goal] == True


@given(user_actions(skip=['rename']))
def test_all_goals_must_be_connected_to_the_root(actions):
    g = Goals('Root')
    note(pretty_print(actions))
    for name, int_val in actions:
        USER_ACTIONS[name](g, int_val)
    edges = g.all(keys='edge')
    queue, visited = [k for k, v in g.all().items() if v == 'Root'], set()
    while queue:
        goal = queue.pop()
        queue.extend(g for g in edges[goal] if g not in visited)
        visited.add(goal)
    assert visited == set(edges.keys())


@given(user_actions(skip=['rename']))
def test_all_open_goals_must_be_connected_to_the_root_via_other_open_goals(actions):
    g = Goals('Root')
    note(pretty_print(actions))
    for name, int_val in actions:
        USER_ACTIONS[name](g, int_val)
    open_goals = set(k for k, v in g.all(keys='open').items() if v)
    edges = {k: v for k, v in g.all(keys='edge').items() if k in open_goals}
    assume(edges)
    queue, visited = [k for k, v in g.all().items() if v == 'Root'], set()
    while queue:
        goal = queue.pop()
        queue.extend(g for g in edges[goal] if g not in visited and g in open_goals)
        visited.add(goal)
    assert visited == set(edges.keys())
