from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Tuple

from siebenapp.domain import Graph, EdgeType, GoalId, RenderResult, Command
from siebenapp.system import save

# Layer is a row of GoalIds, possibly with holes (marked with None)
# E.g.: [17, "3_4", None, 5]
Layer = list[Optional[GoalId]]


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

    def as_tuple(self) -> tuple[int, int]:
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


def safe_average(items: list[int]) -> int:
    return int(sum(items) / len(items)) if items else 0


class Renderer:
    DEFAULT_WIDTH = 4

    def __init__(self, goals: Graph, width_limit=DEFAULT_WIDTH) -> None:
        self.render_result = goals.q()
        self.width_limit = width_limit
        self.rows = self.render_result.rows
        self.node_opts: dict[GoalId, Any] = {row.goal_id: {} for row in self.rows}
        self.edges: dict[GoalId, list[GoalId]] = {
            row.goal_id: [e[0] for e in row.edges] for row in self.rows
        }
        self.back_edges: dict[GoalId, list[GoalId]] = {}
        for row in self.rows:
            for upper_goal, edge_type in row.edges:
                if upper_goal not in self.back_edges:
                    self.back_edges[upper_goal] = []
                self.back_edges[upper_goal].append(row.goal_id)
        self.layers: dict[int, Layer] = defaultdict(list)
        self.positions: dict[GoalId, int] = {}
        self.edge_types: dict[tuple[GoalId, GoalId], EdgeType] = {
            (parent, child): edge_type
            for parent in self.node_opts
            for child, edge_type in self.render_result.by_id(parent).edges
        }
        self.result_edge_options: dict[str, tuple[int, int, int]] = {}

    def build(self) -> RenderResult:
        self.split_by_layers()
        self.reorder()
        self.update_graph()
        self.build_index()
        return RenderResult(
            self.rows,
            edge_opts=self.result_edge_options,
            select=self.render_result.select,
            node_opts=self.node_opts,
        )

    def split_by_layers(self) -> None:
        unsorted_goals: dict[GoalId, list[GoalId]] = dict(self.edges)
        sorted_goals: set[GoalId] = set()
        incoming_edges: set[GoalId] = set()
        outgoing_edges: list[GoalId] = []
        current_layer: int = 0
        while unsorted_goals:
            new_layer: Layer = []
            candidates = self.candidates_for_new_layer(sorted_goals, unsorted_goals)
            for goal, edges_len in candidates:
                unsorted_goals.pop(goal)
                sorted_goals.add(goal)
                new_layer.append(goal)
                back_edges: list[GoalId] = self.back_edges.get(goal, [])
                outgoing_edges.extend(iter(back_edges))
                if len(outgoing_edges) >= self.width_limit:
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

    def candidates_for_new_layer(
        self, sorted_goals: set[GoalId], unsorted_goals: dict[GoalId, list[GoalId]]
    ) -> list[tuple[GoalId, int]]:
        candidates: list[tuple[GoalId, int]] = [
            (goal, len(edges))
            for goal, edges in unsorted_goals.items()
            if all(v in sorted_goals for v in edges)
        ]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[: self.width_limit]

    def reorder(self) -> None:
        for curr_layer in sorted(self.layers.keys(), reverse=True)[:-1]:
            fixed_line: Layer = self.layers[curr_layer]
            random_line: Layer = self.layers[curr_layer - 1]
            deltas: dict[GoalId, int] = self.count_deltas(fixed_line)
            new_positions: dict[GoalId, int] = {
                g: int(self.positions[g] + deltas.get(g, 0))
                for g in random_line
                if g is not None
            }

            placed_line: Layer = self.place(new_positions)
            self.positions |= {
                g: idx for idx, g in enumerate(placed_line) if g is not None
            }
            self.layers[curr_layer - 1] = placed_line

    def count_deltas(self, fixed_line: Layer) -> dict[GoalId, int]:
        deltas: dict[GoalId, list[int]] = defaultdict(list)
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
                if goal_id in self.node_opts:
                    self.node_opts[goal_id]["col"] = real_col
                    real_col += 1
                else:
                    self.node_opts[goal_id] = {
                        "col": col,
                        "edge_render": [],
                    }
                self.node_opts[goal_id] |= {
                    "row": row,
                    "edge_render": [
                        (child, self.edge_types[goal_id, child])
                        for child in self.edges[goal_id]
                    ],
                }

    def build_index(self) -> None:
        result_index: dict[int, dict[int, GoalId]] = {}
        for goal_id, attrs in self.node_opts.items():
            if (row := attrs["row"]) not in result_index:
                result_index[row] = {}
            result_index[row][attrs["col"]] = goal_id

        for row_vals in result_index.values():
            left: int = 0
            edges: list[str] = []
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

    def _write_edges(self, edges: list[str], left: int) -> None:
        self.result_edge_options |= {
            e: (left, i + 1, len(edges) + 1) for i, e in enumerate(edges)
        }

    def place(self, source: dict[GoalId, int]) -> Layer:
        result: Layer = []
        unplaced: list[tuple[GoalId, int]] = sorted(
            [(k, v) for k, v in source.items()], key=goal_key
        )
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


def goal_key(tup: tuple[GoalId, int]) -> tuple[int, int]:
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
    width: dict[int, int] = {}  # key=goal_id
    height: dict[int, int] = {}  # key=goal_id
    max_width: dict[int, int] = {}  # key=column
    max_height: dict[int, int] = {}  # key=row

    for goal_id, attrs in render_result.goals():
        row, col = attrs["row"], attrs["col"]
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
        row, col = attrs["row"], attrs["col"]
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
) -> list[tuple[EdgeType, Point, Point, str]]:
    edges = {}
    lines: list[tuple[EdgeType, Point, Point, str]] = []

    for goal_id, attrs in render_result.node_opts.items():
        for e_target, e_type in attrs["edge_render"]:
            target_attrs = render_result.node_opts[e_target]
            if isinstance(goal_id, int):
                row, col = attrs["row"], attrs["col"]
                start = middle_point(
                    gp.top_left(row, col), gp.top_right(row, col), 1, 2
                )
            else:
                left_id, p, q = render_result.edge_opts[goal_id]
                left = render_result.node_opts[left_id]["col"] if left_id > 0 else -1
                x1 = gp.top_right(attrs["row"], left)
                x2 = gp.top_left(attrs["row"], left + 1)
                start = middle_point(x1, x2, p, q)

                if goal_id not in edges:
                    edges[goal_id] = {"bottom": start, "style": e_type}
                else:
                    edges[goal_id]["bottom"] = start
                    edges[goal_id]["style"] = max(edges[goal_id]["style"], e_type)
            if isinstance(e_target, int):
                row, col = target_attrs["row"], target_attrs["col"]
                end = middle_point(
                    gp.bottom_left(row, col), gp.bottom_right(row, col), 1, 2
                )
            else:
                left_id, p, q = render_result.edge_opts[e_target]
                left = render_result.node_opts[left_id]["col"] if left_id > 0 else -1
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


class GoalsHolder:
    def __init__(self, goals: Graph, filename: str, cache: bool = False):
        self.goals = goals
        self.filename = filename
        self.cache = cache
        self.previous: RenderResult = RenderResult([])

    def accept(self, *actions: Command) -> None:
        if actions:
            self.goals.accept_all(*actions)
        save(self.goals, self.filename)

    def render(self, width: int) -> Tuple[RenderResult, list[GoalId]]:
        """Render tree with a given width and return two values:
        1. Render result as is.
        2. A list of changed rows in case of _partial_ update; empty list otherwise.
        """
        result: RenderResult = Renderer(self.goals, width).build()
        if not self.cache:
            return result, []
        delta = self._calculate_delta(result)
        self.previous = result
        return result, delta

    def _calculate_delta(self, new_result: RenderResult) -> list[GoalId]:
        if len(self.previous.rows) == len(new_result.rows):
            for old_row in self.previous.rows:
                new_row = new_result.by_id(old_row.goal_id)
                if old_row != new_row:
                    # eager exit on any change in rows
                    return []
            result: list[GoalId] = []
            if self.previous.select[0] != new_result.select[0]:
                result.append(self.previous.select[0])
                result.append(new_result.select[0])
            if self.previous.select[1] != new_result.select[1]:
                result.append(self.previous.select[1])
                result.append(new_result.select[1])
            return result
        return []
