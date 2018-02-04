from collections import defaultdict
from functools import partial


class Renderer:
    WIDTH_LIMIT = 4

    def __init__(self, goals):
        self.graph = goals.all(keys='name,edge,open,select,switchable')
        self.edges = {key: values['edge'] for key, values in self.graph.items()}
        self.layers = defaultdict(list)
        self.positions = {}

    def build(self):
        self.split_by_layers()
        self.reorder()
        self.update_graph()
        return self.graph

    def split_by_layers(self):
        unsorted_goals, sorted_goals = dict(self.edges), set()
        current_layer, width_current, width_up = 0, 0, 0
        incoming_edges, outgoing_edges = set(), set()
        while unsorted_goals:
            new_layer = []
            for goal, edges_len in self.candidates_for_new_layer(sorted_goals, unsorted_goals):
                unsorted_goals.pop(goal)
                sorted_goals.add(goal)
                new_layer.append(goal)
                back_edges = [k for k, vs in self.edges.items() if goal in vs]
                outgoing_edges.update(e for e in back_edges)
                width_current += 1 - edges_len
                width_up += len(back_edges)
                if (width_current >= self.WIDTH_LIMIT and edges_len < 1) or (width_up >= self.WIDTH_LIMIT):
                    break
            incoming_edges = incoming_edges.difference(set(new_layer))
            for original_id in incoming_edges:
                new_goal_name = '%d_%d' % (original_id, current_layer)
                self.edges[new_goal_name] = [g for g in self.edges[original_id]
                                             if g in sorted_goals and g not in new_layer]
                for g in self.edges[new_goal_name]:
                    self.edges[original_id].remove(g)
                self.edges[original_id].append(new_goal_name)
                new_layer.append(new_goal_name)
                sorted_goals.add(new_goal_name)
            self.layers[current_layer] = new_layer
            current_layer += 1
            width_current, width_up = width_up, 0
            incoming_edges.update(outgoing_edges)
            outgoing_edges.clear()
        self.positions = {g: idx for layer in self.layers.values() for idx, g in enumerate(layer)}

    @staticmethod
    def candidates_for_new_layer(sorted_goals, unsorted_goals):
        candidates = [(goal, len(edges)) for goal, edges in unsorted_goals.items()
                      if all(v in sorted_goals for v in edges)]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def reorder(self):
        for curr_layer in sorted(self.layers.keys(), reverse=True)[:-1]:
            if self.intersections(curr_layer) == 0:
                continue
            fixed_line = self.layers[curr_layer]
            random_line = self.layers[curr_layer - 1]
            deltas = defaultdict(list)
            for goal in fixed_line:
                for e in self.edges[goal]:
                    deltas[e].append(self.positions[goal] - self.positions[e])

            random_line.sort(key=partial(self.safe_average, deltas))
            self.positions.update({g: idx for idx, g in enumerate(random_line)})
            self.layers[curr_layer - 1] = random_line

    @staticmethod
    def safe_average(deltas, g):
        return sum(deltas[g]) / len(deltas[g]) if deltas[g] else 0

    def intersections(self, layer):
        enumerated_edges = [(self.positions[t], self.positions[e])
                            for t in self.layers[layer]
                            for e in self.edges[t]]
        return len([1 for a in enumerated_edges for b in enumerated_edges
                    if a[0] < b[0] and a[1] > b[1]])

    def update_graph(self):
        for row in sorted(self.layers.keys()):
            for col, goal_id in enumerate(self.layers[row]):
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
                    'edge': self.edges[goal_id],
                })
