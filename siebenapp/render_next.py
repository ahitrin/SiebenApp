from dataclasses import dataclass
from typing import Callable, Any, Optional

from siebenapp.domain import RenderResult, GoalId, Graph


@dataclass
class RenderStep:
    rr: RenderResult
    roots: list[GoalId]
    layers: list[list[GoalId]]
    previous: dict[GoalId, list[GoalId]]


def add_if_not(m: dict, m1: dict) -> dict:
    """Merge two dictionaries _without_ overwriting already existing values."""
    nm = dict(m)
    for k, v in m1.items():
        if nm.get(k, None) is None:
            nm[k] = v
    return nm


def find_previous(rr: RenderResult) -> dict[GoalId, list[GoalId]]:
    """Add previous nodes (parent, blocked, etc) for every node."""
    result: dict[GoalId, list[GoalId]] = {g: [] for g in rr.roots}
    to_visit: set[GoalId] = set(rr.roots)
    while to_visit:
        g = to_visit.pop()
        connections = [e[0] for e in rr.by_id(g).edges]
        for g1 in connections:
            to_visit.add(g1)
            result[g1] = result.get(g1, []) + [g]
    return result


def tube(step: RenderStep, width: int) -> RenderStep:
    """Node placing algorithm that uses a "tube" with a fixed width."""
    new_layer: list[GoalId] = []
    already_added: set[GoalId] = {g for l in step.layers for g in l}
    for goal_id in step.roots:
        if len(new_layer) >= width:
            break
        if all(g in already_added for g in step.previous[goal_id]):
            new_layer.append(goal_id)
    new_roots: list[GoalId] = step.roots[len(new_layer) :] + [
        e[0] for gid in new_layer for e in step.rr.by_id(gid).edges
    ]
    new_opts: dict[GoalId, dict] = {
        goal_id: add_if_not(
            opts,
            {
                "row": len(step.layers) if goal_id in new_layer else None,
                "col": new_layer.index(goal_id) if goal_id in new_layer else None,
            },
        )
        for goal_id, opts in step.rr.node_opts.items()
    }
    new_layers = step.layers + [new_layer]
    already_added.update({g for l in new_layers for g in l})
    filtered_roots: list[GoalId] = []
    for g in new_roots:
        if g not in already_added:
            filtered_roots.append(g)
            already_added.add(g)

    return RenderStep(
        RenderResult(
            step.rr.rows, node_opts=new_opts, select=step.rr.select, roots=step.rr.roots
        ),
        filtered_roots,
        new_layers,
        step.previous,
    )


def build_with(
    rr: RenderResult, fn: Callable[[RenderStep, int], RenderStep], width: int
) -> RenderStep:
    """Invoke node placing algorithm in a loop while there are nodes to place."""
    step = RenderStep(rr, list(rr.roots), [], find_previous(rr))
    while step.roots:
        step = fn(step, width)
    return step


def avg(vals: list) -> float:
    """Safe average for the list (possibly empty)."""
    return sum(vals) / len(vals) if vals else 0


def calc_shift(rr: RenderResult) -> dict[GoalId, float]:
    """Calculate forces that moves each node to the left (negative) or to the right (positive)."""
    connected: dict[GoalId, set[GoalId]] = {row.goal_id: set() for row in rr.rows}
    for row in rr.rows:
        for e in row.edges:
            connected[e[0]].add(row.goal_id)
            connected[row.goal_id].add(e[0])

    result = {}
    for row in rr.rows:
        goal_id = row.goal_id
        opts = rr.node_opts[goal_id]
        row_, col_ = opts["row"], opts["col"]
        deltas = [
            (rr.node_opts[c]["row"] - row_, rr.node_opts[c]["col"] - col_)
            for c in connected[goal_id]
        ]
        result[goal_id] = avg([d[1] for d in deltas])
    return result


def adjust_horizontal(rr: RenderResult, mult: float) -> RenderResult:
    """Move nodes in the horizontal dimension according to the force of the given multiplier."""
    deltas = calc_shift(rr)
    new_opts = {
        goal_id: opts | {"col": opts["col"] + (mult * deltas[goal_id])}
        for goal_id, opts in rr.node_opts.items()
    }
    return RenderResult(rr.rows, node_opts=new_opts, select=rr.select, roots=rr.roots)


def normalize_cols(rr: RenderResult, width: int) -> RenderResult:
    """Convert float column values into integer ones."""
    order0: dict[int, list[tuple[int, GoalId]]] = {}
    for goal_id, opts in rr.node_opts.items():
        row, col = opts["row"], opts["col"]
        if row not in order0:
            order0[row] = []
        order0[row].append((col, goal_id))
    order1: dict[int, list[tuple[int, GoalId]]] = {}
    for layer, tuples in order0.items():
        non_empty = list(round(t[0]) for t in tuples)
        need_drop = len(tuples) - len(set(non_empty))
        empty = {x for x in range(width)}.difference(non_empty)
        for i in range(need_drop):
            empty.pop()
        order1[layer] = tuples + [(e, -10) for e in empty]
    order2: dict[int, list[tuple[int, GoalId]]] = {
        k: sorted(v) for k, v in order1.items()
    }
    indexed0: dict[int, list[GoalId]] = {
        k: [t[1] for t in v] for k, v in order2.items()
    }
    indexed1: dict[GoalId, int] = {
        goal_id: idx
        for layer1 in indexed0.values()
        for idx, goal_id in enumerate(layer1)
        if isinstance(goal_id, int)
    }
    new_opts = {
        goal_id: opts | {"col": indexed1[goal_id]}
        for goal_id, opts in rr.node_opts.items()
    }
    return RenderResult(rr.rows, node_opts=new_opts, select=rr.select, roots=rr.roots)


def __log(listener: Optional[list[tuple[str, Any]]], msg: str, content: Any) -> None:
    """Log a message to the listener, iff it exists."""
    if listener is not None:
        listener.append((msg, content))


def revert_rows(rr: RenderResult) -> RenderResult:
    """Algorithm and UI uses different ordering scheme for rows.
    Here we revert rows order to adapt them to screen requirements."""
    max_row: int = max(o["row"] for o in rr.node_opts.values()) + 1
    node_opts = {k: v | {"row": max_row - v["row"]} for k, v in rr.node_opts.items()}
    return RenderResult(rr.rows, rr.edge_opts, rr.select, node_opts, rr.roots)


def tweak_horizontal(
    rr: RenderResult, width: int, listener: Optional[list[tuple[str, Any]]] = None
) -> RenderResult:
    """Improve horizontal node placement on all layers."""
    r1 = adjust_horizontal(rr, 1.0)
    __log(listener, "Horizontal adjustment 1", r1)
    r2 = adjust_horizontal(r1, 0.5)
    __log(listener, "Horizontal adjustment 2", r2)
    r3 = normalize_cols(r2, width)
    __log(listener, "Normalized columns", r3)
    return r3


def add_edges(rr: RenderResult) -> RenderResult:
    """Workaround: add data needed later by edge rendering algorithm."""
    node_opts = rr.node_opts
    for r in rr.rows:
        node_opts[r.goal_id] |= {"edge_render": r.edges}
    return RenderResult(rr.rows, rr.edge_opts, rr.select, node_opts, rr.roots)


def full_render(
    g: Graph, width: int, listener: Optional[list[tuple[str, Any]]] = None
) -> RenderResult:
    """Main entrance point for the rendering process."""
    r0: RenderResult = g.q()
    r0.node_opts = {row.goal_id: {} for row in r0.rows}
    r1: RenderStep = build_with(r0, tube, width)
    __log(listener, "Graph", r1)
    r2: RenderResult = revert_rows(r1.rr)
    __log(listener, "Invert rows", r2)
    r3: RenderResult = tweak_horizontal(r2, width, listener)
    r4: RenderResult = add_edges(r3)
    __log(listener, "Final result", r4)
    return r4
