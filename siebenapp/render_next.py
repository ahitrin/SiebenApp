from dataclasses import dataclass
from typing import Callable

from siebenapp.domain import RenderResult, GoalId

WIDTH: int = 4


@dataclass
class RenderStep:
    rr: RenderResult
    roots: list[GoalId]
    layers: list[list[GoalId]]
    previous: dict[GoalId, list[GoalId]]


def add_if_not(m: dict, m1: dict) -> dict:
    nm = dict(m)
    for k, v in m1.items():
        if nm.get(k, None) is None:
            nm[k] = v
    return nm


def find_previous(rr: RenderResult) -> dict[GoalId, list[GoalId]]:
    result: dict[GoalId, list[GoalId]] = {g: [] for g in rr.roots}
    to_visit: set[GoalId] = set(rr.roots)
    while to_visit:
        g = to_visit.pop()
        connections = [e[0] for e in rr.by_id(g).edges]
        for g1 in connections:
            to_visit.add(g1)
            result[g1] = result.get(g1, []) + [g]
    return result


def tube(step: RenderStep):
    new_layer: list[GoalId] = []
    already_added: set[GoalId] = set(g for l in step.layers for g in l)
    for goal_id in step.roots:
        if len(new_layer) >= WIDTH:
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
    already_added.update(set(g for l in new_layers for g in l))
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


def build_with(rr: RenderResult, fn: Callable[[RenderStep], RenderStep]) -> RenderStep:
    step = RenderStep(rr, list(rr.roots), [], find_previous(rr))
    while step.roots:
        step = fn(step)
    return step


def avg(vals):
    return sum(vals) / len(vals)


def shift_neutral(ds):
    return avg([d[1] for d in ds])


def calc_shift(rr: RenderResult, shift_fn):
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
        result[goal_id] = shift_fn(deltas)
    return result


def adjust_horizontal(rr: RenderResult, mult):
    deltas = calc_shift(rr, shift_neutral)
    new_opts = {
        goal_id: opts | {"col": opts["col"] + (mult * deltas[goal_id])}
        for goal_id, opts in rr.node_opts.items()
    }
    return RenderResult(rr.rows, node_opts=new_opts, select=rr.select, roots=rr.roots)


def normalize_cols(rr: RenderResult) -> RenderResult:
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
        empty = {x for x in range(WIDTH)}.difference(non_empty)
        for i in range(need_drop):
            empty.pop()
        order1[layer] = tuples + [(e, -10) for e in empty]
    order2: dict[int, list[tuple[int, GoalId]]] = {
        k: sorted(v) for k, v in order1.items()
    }
    indexed0: dict[int, list[GoalId]] = {
        k: [t[1] for t in v] for k, v in order2.items()
    }
    indexed1: dict[GoalId, int] = {}
    for layer1 in indexed0.values():
        for i, goal_id in enumerate(layer1):
            if isinstance(goal_id, int) and goal_id > 0:
                indexed1[goal_id] = i
    new_opts = {
        goal_id: opts | {"col": indexed1[goal_id]}
        for goal_id, opts in rr.node_opts.items()
    }
    return RenderResult(rr.rows, node_opts=new_opts, select=rr.select, roots=rr.roots)
