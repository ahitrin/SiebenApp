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


@given(user_actions(), choices())
def test_any_goal_may_be_selected(actions, choice):
    # skip actions having 'select' at the end
    assume(actions)
    assume(actions[-1][0] != 'select' if actions else True)
    note(pretty_print(actions))
    g = Goals('Root')
    for name, int_val in actions:
        USER_ACTIONS[name](g, int_val)
    rnd_goal = choice(list(g.all().keys()))
    note('Select: %d' % rnd_goal)
    for i in str(rnd_goal):
        g.select(int(i))
    assert g.all(keys='select')[rnd_goal] == True


@given(user_actions())
def test_all_goals_must_be_connected_to_the_root(actions):
    # skip actions that may rename the root goal
    assume(all(action[0] != 'rename' for action in actions))
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


@given(user_actions())
def test_all_open_goals_must_be_connected_to_the_root_via_other_open_goals(actions):
    # skip actions that may rename the root goal
    assume(all(action[0] != 'rename' for action in actions))
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
