from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union, Any, Set, Optional, Protocol

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

    def goals(self):
        return [
            (goal_id, attrs)
            for goal_id, attrs in self.graph.items()
            if isinstance(goal_id, int)
        ]


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, multiplier: float) -> "Point":
        return Point(int(self.x * multiplier), int(self.y * multiplier))

    def __truediv__(self, divisor: float) -> "Point":
        return Point(int(self.x / divisor), int(self.y / divisor))

    def __repr__(self):
        return f"<{self.x}, {self.y}>"

    def as_tuple(self) -> Tuple[int, int]:
        return self.x, self.y


class GeometryProvider(Protocol):
    def top_left(self, row: int, col: int) -> Point:
        raise NotImplementedError

    def top_right(self, row: int, col: int) -> Point:
        raise NotImplementedError

    def bottom_left(self, row: int, col: int) -> Point:
        raise NotImplementedError

    def bottom_right(self, row: int, col: int) -> Point:
        raise NotImplementedError


def safe_average(items: List[int]) -> int:
    return int(sum(items) / len(items)) if items else 0


class Renderer:
    DEFAULT_WIDTH = 4

    def __init__(self, goals: Graph, width_limit=DEFAULT_WIDTH) -> None:
        self.width_limit = width_limit
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
        self.merge_cols()
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
                if (len(new_layer) >= self.width_limit and edges_len < 1) or (
                    len(outgoing_edges) >= self.width_limit
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

            placed_line: Layer = self.place(new_positions)
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
                        "edge_render": [],
                        "switchable": False,
                        "select": None,
                        "open": True,
                    }
                self.graph[goal_id].update(
                    {
                        "row": row,
                        "col": col,
                        "edge_render": [
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

    def place(self, source: Dict[GoalId, int]) -> Layer:
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
        while len(result) > self.width_limit and None in result:
            result.remove(None)
        return result

    def merge_cols(self):
        for goal_id, attrs in self.graph.items():
            if isinstance(goal_id, int):
                attrs["col"] = attrs["col1"]


def goal_key(tup: Tuple[GoalId, int]) -> Tuple[int, int]:
    """Sort goals by position first and by id second (transform str ids into ints)"""
    goal_id, goal_pos = tup
    if isinstance(goal_id, str):
        return goal_pos, int(goal_id.split("_")[0])
    return goal_pos, goal_id


def middle_point(left: Point, right: Point, numerator: int, denominator: int) -> Point:
    return left + (right - left) * numerator / denominator


def adjust_graph(render_result: RenderResult, gp: GeometryProvider) -> None:
    min_x: int = 100000
    max_x: int = 0
    min_y: int = 100000
    max_y: int = 0
    max_col: int = 0
    max_row: int = 0
    width: Dict[int, int] = {}  # key=goal_id
    height: Dict[int, int] = {}  # key=goal_id
    max_width: Dict[int, int] = {}  # key=column
    max_height: Dict[int, int] = {}  # key=row

    for goal_id, attrs in render_result.goals():
        row, col = attrs["row"], attrs["col1"]
        max_row = max([max_row, row])
        max_col = max([max_col, col])
        tl = gp.top_left(row, col)
        x, y = tl.x, tl.y
        min_x = min([min_x, x])
        max_x = max([max_x, x])
        min_y = min([min_y, y])
        max_y = max([max_y, y])
        width[goal_id] = (gp.top_right(row, col) - tl).x
        max_width[col] = max([max_width.get(col, 0), width[goal_id]])
        height[goal_id] = (gp.bottom_left(row, col) - tl).y
        max_height[row] = max([max_height.get(row, 0), height[goal_id]])

    gap_x = int(
        (max_width[max_col] + max_x - min_x - sum(max_width.values()))
        / (len(max_width) - 1)
        if len(max_width) > 1
        else 50
    )
    gap_y = int(
        (max_height[max_row] + max_y - min_y - sum(max_height.values()))
        / (len(max_height) - 1)
        if len(max_height) > 1
        else 30
    )

    for goal_id, attrs in render_result.goals():
        row, col = attrs["row"], attrs["col1"]
        attrs["x"] = (
            min_x
            + sum(max_width[i] for i in range(col))
            + (col * gap_x)
            + ((max_width[col] - width[goal_id]) // 2)
        )
        attrs["y"] = (
            min_y
            + sum(max_height[i] for i in range(row))
            + (row * gap_y)
            + ((max_height[row] - height[goal_id]) // 2)
        )


def render_lines(
    gp: GeometryProvider, render_result: RenderResult
) -> List[Tuple[EdgeType, Point, Point, str]]:
    edges = {}
    lines: List[Tuple[EdgeType, Point, Point, str]] = []

    for goal_id, attrs in render_result.graph.items():
        for e_target, e_type in attrs["edge_render"]:
            target_attrs = render_result.graph[e_target]
            if isinstance(goal_id, int):
                row, col1 = attrs["row"], attrs["col1"]
                start = middle_point(
                    gp.top_left(row, col1), gp.top_right(row, col1), 1, 2
                )
            else:
                left_id, p, q = render_result.edge_opts[goal_id]
                left = render_result.graph[left_id]["col1"] if left_id > 0 else -1
                x1 = gp.top_right(attrs["row"], left)
                x2 = gp.top_left(attrs["row"], left + 1)
                start = middle_point(x1, x2, p, q)

                if goal_id not in edges:
                    edges[goal_id] = {"bottom": start, "style": e_type}
                else:
                    edges[goal_id]["bottom"] = start
                    edges[goal_id]["style"] = max(edges[goal_id]["style"], e_type)
            if isinstance(e_target, int):
                row, col1 = target_attrs["row"], target_attrs["col1"]
                end = middle_point(
                    gp.bottom_left(row, col1), gp.bottom_right(row, col1), 1, 2
                )
            else:
                left_id, p, q = render_result.edge_opts[e_target]
                left = render_result.graph[left_id]["col1"] if left_id > 0 else -1
                x1 = gp.bottom_right(target_attrs["row"], left)
                x2 = gp.bottom_left(target_attrs["row"], left + 1)
                end = middle_point(x1, x2, p, q)

                if e_target not in edges:
                    edges[e_target] = {"top": end, "style": e_type}
                else:
                    edges[e_target]["top"] = end
                    edges[e_target]["style"] = max(edges[e_target]["style"], e_type)
            lines.append((e_type, start, end, f"{goal_id}-{e_target}"))

    for e in edges.values():
        lines.append((e["style"], e["bottom"], e["top"], ""))

    return lines
