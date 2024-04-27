from dataclasses import dataclass
from typing import Callable

from siebenapp.domain import RenderResult

WIDTH: int = 4


@dataclass
class RenderStep:
    rr: RenderResult
    roots: list[int]
    layers: list[list[int]]
    previous: dict[int, list[int]]


def add_if_not(m: dict, m1: dict) -> dict:
    nm = dict(m)
    for k, v in m1.items():
        if nm.get(k, None) is None:
            nm[k] = v
    return nm


def find_previous(rr: RenderResult) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {g: [] for g in rr.roots}
    to_visit: set[int] = set(rr.roots)
    while to_visit:
        g = to_visit.pop()
        connections = [e[0] for e in rr.by_id(g).edges]
        for g1 in connections:
            to_visit.add(g1)
            result[g1] = result.get(g1, []) + [g]
    return result


def tube(step: RenderStep):
    new_layer: list[int] = []
    already_added: set[int] = set(g for l in step.layers for g in l)
    for goal_id in step.roots:
        if len(new_layer) >= WIDTH:
            break
        if all(g in already_added for g in step.previous[goal_id]):
            new_layer.append(goal_id)
    new_roots: list[int] = step.roots[len(new_layer) :] + [
        e[0] for gid in new_layer for e in step.rr.by_id(gid).edges
    ]
    new_opts: dict[int, dict] = {
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
    filtered_roots: list[int] = []
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
