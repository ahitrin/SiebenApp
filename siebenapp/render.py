from collections import defaultdict
from typing import Dict, List, Tuple, Union, Any, Set

from siebenapp.domain import Graph
from siebenapp.goaltree import EdgeType


def safe_average(l: List[int]) -> int:
    return sum(l) / len(l) if l else 0


class Renderer:
    WIDTH_LIMIT = 4

    def __init__(self, goals: Graph) -> None:
        self.graph = goals.q(keys='name,edge,open,select,switchable')
        self.edges = {key: [e[0] for e in values['edge']] for key, values in self.graph.items()}
        self.layers = defaultdict(list)     # type: Dict[int, List[int]]
        self.positions = {}                 # type: Dict[int, int]
        self.edge_types = {
            (parent, child): edge_type
            for parent in self.graph
            for child, edge_type in self.graph[parent]['edge']
        }                                   # type: Dict[Tuple[Union[str, int], Union[str, int]], int]

    def build(self) -> Dict[int, Any]:
        self.split_by_layers()
        self.reorder()
        self.update_graph()
        return self.graph

    def split_by_layers(self) -> None:
        unsorted_goals = dict(self.edges)   # type: Dict[int, List[int]]
        sorted_goals = set()                # type: Set[Union[int, str]]
        incoming_edges = set()              # type: Set[int]
        outgoing_edges = set()              # type: Set[int]
        current_layer = 0
        while unsorted_goals:
            new_layer = []                  # type: List[Union[int, str]]
            for goal, edges_len in self.candidates_for_new_layer(sorted_goals, unsorted_goals):
                unsorted_goals.pop(goal)
                sorted_goals.add(goal)
                new_layer.append(goal)
                back_edges = [k for k, vs in self.edges.items() if goal in vs]
                outgoing_edges.update(e for e in back_edges)
                if (len(new_layer) >= self.WIDTH_LIMIT and edges_len < 1) or \
                        (len(outgoing_edges) >= self.WIDTH_LIMIT):
                    break
            incoming_edges = incoming_edges.difference(set(new_layer))
            for original_id in incoming_edges:
                new_goal_name = '%d_%d' % (original_id, current_layer)
                self.edges[new_goal_name] = [g for g in self.edges[original_id]
                                             if g in sorted_goals and g not in new_layer]
                new_edge_type = EdgeType.BLOCKER
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
        self.positions = {g: idx for layer in self.layers.values() for idx, g in enumerate(layer)}

    @staticmethod
    def candidates_for_new_layer(sorted_goals: Set[Union[int, str]],
                                 unsorted_goals: Dict[int, List[int]]
                                 ) -> List[Tuple[int, int]]:
        candidates = [(goal, len(edges)) for goal, edges in unsorted_goals.items()
                      if all(v in sorted_goals for v in edges)]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def reorder(self) -> None:
        for curr_layer in sorted(self.layers.keys(), reverse=True)[:-1]:
            fixed_line = self.layers[curr_layer]
            random_line = self.layers[curr_layer - 1]
            deltas = self.count_deltas(fixed_line)
            new_positions = {g: int(self.positions[g] + deltas.get(g, 0))
                             for g in random_line}

            random_line = place(new_positions)
            self.positions.update({g: idx for idx, g in enumerate(random_line)})
            self.layers[curr_layer - 1] = random_line

    def count_deltas(self, fixed_line):
        deltas = defaultdict(list)      # type: Dict[int, List[int]]
        for goal in fixed_line:
            if goal is not None:
                for e in self.edges[goal]:
                    deltas[e].append(self.positions[goal] - self.positions[e])
        return {k: safe_average(v) for k, v in deltas.items()}

    def intersections(self, layer):
        enumerated_edges = [(self.positions[t], self.positions[e])
                            for t in self.layers[layer]
                            for e in self.edges[t]]
        return len([1 for a in enumerated_edges for b in enumerated_edges
                    if a[0] < b[0] and a[1] > b[1]])

    def update_graph(self):
        for row in sorted(self.layers.keys()):
            for col, goal_id in enumerate(self.layers[row]):
                if goal_id is None:
                    continue
                if goal_id not in self.graph:
                    self.graph[goal_id] = {
                        'name': '',
                        'edge': [],
                        'switchable': False,
                        'select': None,
                        'open': True,
                    }
                self.graph[goal_id].update({
                    'row': row,
                    'col': col,
                    'edge': [(child, self.edge_types[goal_id, child]) for child in self.edges[goal_id]],
                })


def place(source):
    result = []
    unsorted = sorted(list(source.items()), key=goal_key)
    while unsorted:
        value, index = unsorted.pop(0)
        if len(result) < index + 1:
            result.extend([None] * (index + 1 - len(result)))
        if result[index] is None:
            result[index] = value
        else:
            unsorted.insert(0, (value, index + 1))
    while len(result) > 4 and None in result:
        result.remove(None)
    return result


def goal_key(tup):
    """Sort goals by position first and by id second (transform str ids into ints)"""
    goal_id, goal_pos = tup
    if isinstance(goal_id, str):
        return goal_pos, int(goal_id.split('_')[0])
    return goal_pos, goal_id
