from collections import defaultdict


def safe_average(l):
    return sum(l) / len(l) if l else 0


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
        incoming_edges, outgoing_edges = set(), set()
        current_layer = 0
        while unsorted_goals:
            new_layer = []
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
                for g in self.edges[new_goal_name]:
                    self.edges[original_id].remove(g)
                self.edges[original_id].append(new_goal_name)
                new_layer.append(new_goal_name)
                sorted_goals.add(new_goal_name)
            self.layers[current_layer] = new_layer
            current_layer += 1
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
            fixed_line = self.layers[curr_layer]
            random_line = self.layers[curr_layer - 1]
            deltas = self.count_deltas(fixed_line)
            new_positions = {g: int(self.positions[g] + deltas[g])
                             for g in random_line}

            random_line = place(new_positions)
            self.positions.update({g: idx for idx, g in enumerate(random_line)})
            self.layers[curr_layer - 1] = random_line

    def count_deltas(self, fixed_line):
        deltas = defaultdict(list)
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
                    'edge': self.edges[goal_id],
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
