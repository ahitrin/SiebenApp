from dataclasses import dataclass

from siebenapp.domain import EdgeType
from siebenapp.goaltree import Goals


@dataclass(frozen=True)
class GoalPrototype:
    goal_id: int
    name: str
    open: bool
    children: list[int]
    blockers: list[int]
    relations: list[int]


def _build_goal_prototype(goal_id, name, is_open, children, blockers, relations):
    children = children or []
    blockers = blockers or []
    relations = relations or []
    assert isinstance(children, list)
    return GoalPrototype(goal_id, name, is_open, children, blockers, relations)


def open_(goal_id, name, children=None, blockers=None, relations=None):
    return _build_goal_prototype(goal_id, name, True, children, blockers, relations)


def clos_(goal_id, name, children=None, blockers=None, relations=None):
    return _build_goal_prototype(goal_id, name, False, children, blockers, relations)


def build_goaltree(*goal_prototypes, select: tuple[int, int], message_fn=None) -> Goals:
    goals = [(g.goal_id, g.name, g.open) for g in goal_prototypes]
    edges = []
    for g in goal_prototypes:
        edges.extend([(g.goal_id, e, EdgeType.PARENT) for e in g.children])
        edges.extend([(g.goal_id, e, EdgeType.BLOCKER) for e in g.blockers])
        edges.extend([(g.goal_id, e, EdgeType.RELATION) for e in g.relations])
    selection_id, prev_selection_id = select
    all_ids = {g.goal_id for g in goal_prototypes}
    assert selection_id in all_ids
    assert prev_selection_id in all_ids
    return Goals.build(
        goals,
        edges,
        message_fn,
    )
