from dataclasses import dataclass

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
    children: list[int]
    blockers: list[int]
    relations: list[int]
    select: str | None


def _build_goal_prototype(
    goal_id, name, is_open, children, blockers, relations, select
):
    children = children or []
    blockers = blockers or []
    relations = relations or []
    assert isinstance(children, list)
    assert select in allowed_selects
    return GoalPrototype(goal_id, name, is_open, children, blockers, relations, select)


def open_(goal_id, name, children=None, blockers=None, relations=None, select=None):
    return _build_goal_prototype(
        goal_id, name, True, children, blockers, relations, select
    )


def clos_(goal_id, name, children=None, blockers=None, relations=None, select=None):
    return _build_goal_prototype(
        goal_id, name, False, children, blockers, relations, select
    )


def build_goaltree(
    *goal_prototypes, select: tuple[int, int] | None = None, message_fn=None
) -> Goals:
    goals = [(g.goal_id, g.name, g.open) for g in goal_prototypes]
    edges = []
    for g in goal_prototypes:
        edges.extend([(g.goal_id, e, EdgeType.PARENT) for e in g.children])
        edges.extend([(g.goal_id, e, EdgeType.BLOCKER) for e in g.blockers])
        edges.extend([(g.goal_id, e, EdgeType.RELATION) for e in g.relations])
    if select is not None:
        # New logic
        selection_id, prev_selection_id = select
        all_ids = {g.goal_id for g in goal_prototypes}
        assert selection_id in all_ids
        assert prev_selection_id in all_ids
    else:
        # Legacy logic
        selection = {g.goal_id for g in goal_prototypes if g.select == selected}
        prev_selection = {g.goal_id for g in goal_prototypes if g.select == previous}
        assert len(selection) == 1
        assert len(prev_selection) <= 1
        selection_id = selection.pop()
        prev_selection_id = prev_selection.pop() if prev_selection else selection_id
    return Goals.build(
        goals,
        edges,
        [
            ("selection", selection_id),
            (
                "previous_selection",
                prev_selection_id,
            ),
        ],
        message_fn,
    )
