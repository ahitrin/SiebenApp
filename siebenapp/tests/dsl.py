from collections import namedtuple

from siebenapp.goaltree import Goals, Edge

selected = 'select'
previous = 'previous'
allowed_selects = {selected, previous, None}
GoalPrototype = namedtuple('GoalPrototype', 'id name open children blockers select')


def _build_goal_prototype(goal_id, name, is_open, children, blockers, select):  # pylint: disable=too-many-arguments
    children = [] if children is None else children
    blockers = [] if blockers is None else blockers
    assert isinstance(children, list)
    assert select in allowed_selects
    return GoalPrototype(goal_id, name, is_open, children, blockers, select)


def open_(goal_id, name, children=None, blockers=None, select=None):
    return _build_goal_prototype(goal_id, name, True, children, blockers, select)


def clos_(goal_id, name, children=None, blockers=None, select=None):
    return _build_goal_prototype(goal_id, name, False, children, blockers, select)


def build_goaltree(*goal_prototypes, message_fn=None):
    goals = [(g.id, g.name, g.open) for g in goal_prototypes]
    edges = [(g.id, e, Edge.PARENT) for g in goal_prototypes for e in g.children] + \
            [(g.id, e, Edge.BLOCKER) for g in goal_prototypes for e in g.blockers]
    selection = {g.id for g in goal_prototypes if g.select == selected}
    prev_selection = {g.id for g in goal_prototypes if g.select == previous}
    assert len(selection) == 1
    assert len(prev_selection) <= 1
    selection_id = selection.pop()
    return Goals.build(goals, edges, [
        ('selection', selection_id),
        ('previous_selection', prev_selection.pop() if prev_selection else selection_id),
    ], message_fn, True)
