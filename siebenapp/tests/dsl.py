from collections import namedtuple

from siebenapp.goaltree import Goals

selected = 'select'
previous = 'previous'
allowed_selects = {selected, previous, None}
GoalPrototype = namedtuple('GoalPrototype', 'id name open edges select')


def _build_goal_prototype(goal_id, name, is_open, edges, select):
    edges = [] if edges is None else edges
    assert isinstance(edges, list)
    assert select in allowed_selects
    return GoalPrototype(goal_id, name, is_open, edges, select)


def open_(goal_id, name, edges=None, select=None):
    return _build_goal_prototype(goal_id, name, True, edges, select)


def clos_(goal_id, name, edges=None, select=None):
    return _build_goal_prototype(goal_id, name, False, edges, select)


def build_goaltree(*goal_prototypes, message_fn=None):
    goals = [(g.id, g.name, g.open) for g in goal_prototypes]
    edges = [(g.id, e) for g in goal_prototypes for e in g.edges]
    selection = {g.id for g in goal_prototypes if g.select == selected}
    prev_selection = {g.id for g in goal_prototypes if g.select == previous}
    assert len(selection) == 1
    assert len(prev_selection) <= 1
    selection_id = selection.pop()
    return Goals.build(goals, edges, {
        'selection': selection_id,
        'previous_selection': prev_selection.pop() if prev_selection else selection_id
    }, message_fn)
