from dataclasses import dataclass
from typing import List, Optional

from siebenapp.domain import EdgeType
from siebenapp.goaltree import Goals

selected = "select"
previous = "previous"
allowed_selects = {selected, previous, None}


@dataclass(frozen=True)
class GoalPrototype:
    goal_id: int
    name: str
    open: bool
    children: List[int]
    blockers: List[int]
    select: Optional[str]


def _build_goal_prototype(
    goal_id, name, is_open, children, blockers, select
):  # pylint: disable=too-many-arguments
    children = children or []
    blockers = blockers or []
    assert isinstance(children, list)
    assert select in allowed_selects
    return GoalPrototype(goal_id, name, is_open, children, blockers, select)


def open_(goal_id, name, children=None, blockers=None, select=None):
    return _build_goal_prototype(goal_id, name, True, children, blockers, select)


def clos_(goal_id, name, children=None, blockers=None, select=None):
    return _build_goal_prototype(goal_id, name, False, children, blockers, select)


def build_goaltree(*goal_prototypes, message_fn=None):
    goals = [(g.goal_id, g.name, g.open) for g in goal_prototypes]
    edges = [
        (g.goal_id, e, EdgeType.PARENT) for g in goal_prototypes for e in g.children
    ] + [(g.goal_id, e, EdgeType.BLOCKER) for g in goal_prototypes for e in g.blockers]
    selection = {g.goal_id for g in goal_prototypes if g.select == selected}
    prev_selection = {g.goal_id for g in goal_prototypes if g.select == previous}
    assert len(selection) == 1
    assert len(prev_selection) <= 1
    selection_id = selection.pop()
    return Goals.build(
        goals,
        edges,
        [
            ("selection", selection_id),
            (
                "previous_selection",
                prev_selection.pop() if prev_selection else selection_id,
            ),
        ],
        message_fn,
    )
