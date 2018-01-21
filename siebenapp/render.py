from collections import defaultdict


def render_tree(goals):
    return Renderer(goals).build()


class Renderer:
    WIDTH_LIMIT = 4

    def __init__(self, goals):
        self.goals = goals
        self.edges = {}
        self.layers = defaultdict(list)

    def build(self):
        graph = self.goals.all(keys='name,edge,open,select,switchable')
        self.edges = {key: values['edge'] for key, values in graph.items()}
        self.split_by_layers()
        self.reorder()
        self.update_graph(graph)
        return graph

    def split_by_layers(self):
        unsorted_goals, sorted_goals = dict(self.edges), set()
        current_layer, width_current, width_up = 0, 0, 0
        incoming_edges, outgoing_edges = set(), set()
        while unsorted_goals:
            candidates = [(goal, len(edges)) for goal, edges in unsorted_goals.items()
                          if all(v in sorted_goals for v in edges)]
            candidates.sort(key=lambda x: x[1], reverse=True)
            for goal, edges_len in candidates:
                unsorted_goals.pop(goal)
                sorted_goals.add(goal)
                if goal in incoming_edges:
                    incoming_edges.remove(goal)
                self.layers[current_layer].append(goal)
                back_edges = [k for k, vs in self.edges.items() if goal in vs]
                outgoing_edges.update(e for e in back_edges)
                width_current += 1 - edges_len
                width_up += len(back_edges)
                if (width_current >= self.WIDTH_LIMIT and edges_len < 1) or (width_up >= self.WIDTH_LIMIT):
                    break
            for original_id in incoming_edges:
                new_goal_name = '%d_%d' % (original_id, current_layer)
                self.edges[new_goal_name] = [g for g in self.edges[original_id]
                                             if g in sorted_goals and g not in self.layers[current_layer]]
                for g in self.edges[new_goal_name]:
                    self.edges[original_id].remove(g)
                self.edges[original_id].append(new_goal_name)
                self.layers[current_layer].append(new_goal_name)
                sorted_goals.add(new_goal_name)
            current_layer += 1
            width_current, width_up = width_up, 0
            incoming_edges.update(outgoing_edges)
            outgoing_edges.clear()

    def reorder(self):
        for curr_layer in sorted(self.layers.keys(), reverse=True)[:-1]:
            fixed_line = self.layers[curr_layer]
            fixed_positions = {g: i for i, g in enumerate(fixed_line)}
            random_line = self.layers[curr_layer - 1]
            random_positions = {g: i for i, g in enumerate(random_line)}
            deltas = defaultdict(list)
            for goal in fixed_line:
                for e in self.edges[goal]:
                    deltas[e].append(fixed_positions[goal] - random_positions[e])
            gravity = []
            for goal in random_line:
                goal_deltas = deltas[goal]
                force = sum(goal_deltas) / len(goal_deltas) if goal_deltas else 0
                gravity.append((goal, force))
            new_line = [g for g, f in sorted(gravity, key=lambda x: x[1])]
            self.layers[curr_layer - 1] = new_line

    def update_graph(self, graph):
        for row in sorted(self.layers.keys()):
            for col, goal_id in enumerate(self.layers[row]):
                if goal_id not in graph:
                    graph[goal_id] = {
                        'name': '',
                        'edge': [],
                        'switchable': False,
                        'select': None,
                        'open': True,
                    }
                graph[goal_id].update({
                    'row': row,
                    'col': col,
                    'edge': self.edges[goal_id],
                })
