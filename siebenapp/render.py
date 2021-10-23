from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union, Any, Set, Optional

from siebenapp.domain import Graph, EdgeType


# GoalId for real nodes is integer: -1, 4, 34, etc
# GoalId for fake nodes (used to build edges) is str: '3_5', '1_1', etc
GoalId = Union[str, int]
# Layer is a row of GoalIds, possibly with holes (marked with None)
# E.g.: [17, "3_4", None, 5]
Layer = List[Optional[GoalId]]


@dataclass(frozen=True)
class RenderResult:
    graph: Dict[GoalId, Any]
    edge_opts: Dict[str, Tuple[int, int, int]]


def safe_average(items: List[int]) -> int:
    return int(sum(items) / len(items)) if items else 0


class Renderer:
    WIDTH_LIMIT = 4

    def __init__(self, goals: Graph) -> None:
        original_graph: Dict[int, Any] = goals.q(
            keys="name,edge,open,select,switchable"
        )
        self.graph: Dict[GoalId, Any] = {k: v for k, v in original_graph.items()}
        self.edges: Dict[GoalId, List[GoalId]] = {
            key: [e[0] for e in values["edge"]] for key, values in self.graph.items()
        }
        self.layers: Dict[int, Layer] = defaultdict(list)
        self.positions: Dict[GoalId, int] = {}
        self.edge_types: Dict[Tuple[GoalId, GoalId], EdgeType] = {
            (parent, child): edge_type
            for parent in self.graph
            for child, edge_type in self.graph[parent]["edge"]
        }
        self.result_edge_options: Dict[str, Tuple[int, int, int]] = {}

    def build(self) -> RenderResult:
        self.split_by_layers()
        self.reorder()
        self.update_graph()
        self.build_index()
        return RenderResult(self.graph, self.result_edge_options)

    def split_by_layers(self) -> None:
        unsorted_goals: Dict[GoalId, List[GoalId]] = dict(self.edges)
        sorted_goals: Set[GoalId] = set()
        incoming_edges: Set[GoalId] = set()
        outgoing_edges: List[GoalId] = []
        current_layer: int = 0
        while unsorted_goals:
            new_layer: Layer = []
            for goal, edges_len in self.candidates_for_new_layer(
                sorted_goals, unsorted_goals
            ):
                unsorted_goals.pop(goal)
                sorted_goals.add(goal)
                new_layer.append(goal)
                back_edges: List[GoalId] = [
                    k for k, vs in self.edges.items() if goal in vs
                ]
                outgoing_edges.extend(iter(back_edges))
                if (len(new_layer) >= self.WIDTH_LIMIT and edges_len < 1) or (
                    len(outgoing_edges) >= self.WIDTH_LIMIT
                ):
                    break
            incoming_edges = incoming_edges.difference(set(new_layer))
            for original_id in incoming_edges:
                new_goal_name: str = f"{original_id}_{current_layer}"
                self.edges[new_goal_name] = [
                    g
                    for g in self.edges[original_id]
                    if g in sorted_goals and g not in new_layer
                ]
                new_edge_type: EdgeType = EdgeType.BLOCKER
                for g in self.edges[new_goal_name]:
                    self.edges[original_id].remove(g)
                    self.edge_types[new_goal_name, g] = self.edge_types[original_id, g]
                    new_edge_type = max(new_edge_type, self.edge_types[original_id, g])
                self.edges[original_id].append(new_goal_name)
                self.edge_types[original_id, new_goal_name] = new_edge_type
                new_layer.append(new_goal_name)
                sorted_goals.add(new_goal_name)
            self.layers[current_layer] = new_layer
            current_layer += 1
            incoming_edges.update(outgoing_edges)
            outgoing_edges.clear()
        self.positions = {
            g: idx
            for layer in self.layers.values()
            for idx, g in enumerate(layer)
            if g is not None
        }

    @staticmethod
    def candidates_for_new_layer(
        sorted_goals: Set[GoalId], unsorted_goals: Dict[GoalId, List[GoalId]]
    ) -> List[Tuple[GoalId, int]]:
        candidates: List[Tuple[GoalId, int]] = [
            (goal, len(edges))
            for goal, edges in unsorted_goals.items()
            if all(v in sorted_goals for v in edges)
        ]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def reorder(self) -> None:
        for curr_layer in sorted(self.layers.keys(), reverse=True)[:-1]:
            fixed_line: Layer = self.layers[curr_layer]
            random_line: Layer = self.layers[curr_layer - 1]
            deltas: Dict[GoalId, int] = self.count_deltas(fixed_line)
            new_positions: Dict[GoalId, int] = {
                g: int(self.positions[g] + deltas.get(g, 0))
                for g in random_line
                if g is not None
            }

            placed_line: Layer = place(new_positions)
            self.positions.update(
                {g: idx for idx, g in enumerate(placed_line) if g is not None}
            )
            self.layers[curr_layer - 1] = placed_line

    def count_deltas(self, fixed_line: Layer) -> Dict[GoalId, int]:
        deltas: Dict[GoalId, List[int]] = defaultdict(list)
        for goal in fixed_line:
            if goal is not None:
                for e in self.edges[goal]:
                    deltas[e].append(self.positions[goal] - self.positions[e])
        return {k: safe_average(v) for k, v in deltas.items()}

    def update_graph(self) -> None:
        for row in sorted(self.layers.keys()):
            real_col: int = 0
            for col, goal_id in enumerate(self.layers[row]):
                if goal_id is None:
                    continue
                if goal_id in self.graph:
                    self.graph[goal_id]["col1"] = real_col
                    real_col += 1
                else:
                    self.graph[goal_id] = {
                        "name": "",
                        "edge": [],
                        "switchable": False,
                        "select": None,
                        "open": True,
                    }
                self.graph[goal_id].update(
                    {
                        "row": row,
                        "col": col,
                        "edge": [
                            (child, self.edge_types[goal_id, child])
                            for child in self.edges[goal_id]
                        ],
                    }
                )

    def build_index(self) -> None:
        result_index: Dict[int, Dict[int, GoalId]] = {}
        for goal_id, attrs in self.graph.items():
            if (row := attrs["row"]) not in result_index:
                result_index[row] = {}
            result_index[row][attrs["col"]] = goal_id

        for row_vals in result_index.values():
            left: int = 0
            edges: List[str] = []
            phase: str = "goals"

            for _, new_goal_id in sorted(row_vals.items(), key=lambda x: x[0]):
                if isinstance(new_goal_id, int):
                    if phase == "edges":
                        self._write_edges(edges, left)
                        edges = []
                    phase = "goals"
                    left = new_goal_id
                else:
                    phase = "edges"
                    edges.append(new_goal_id)
            self._write_edges(edges, left)

    def _write_edges(self, edges: List[str], left: int) -> None:
        self.result_edge_options.update(
            {e: (left, i + 1, len(edges) + 1) for i, e in enumerate(edges)}
        )


def place(source: Dict[GoalId, int]) -> Layer:
    result: Layer = []
    unplaced: List[Tuple[GoalId, int]] = sorted(list(source.items()), key=goal_key)
    while unplaced:
        value, index = unplaced.pop(0)
        if len(result) < index + 1:
            result.extend([None] * (index + 1 - len(result)))
        if result[index] is None:
            result[index] = value
        else:
            unplaced.insert(0, (value, index + 1))
    while len(result) > 4 and None in result:
        result.remove(None)
    return result


def goal_key(tup: Tuple[GoalId, int]) -> Tuple[int, GoalId]:
    """Sort goals by position first and by id second (transform str ids into ints)"""
    goal_id, goal_pos = tup
    if isinstance(goal_id, str):
        return goal_pos, int(goal_id.split("_")[0])
    return goal_pos, goal_id
