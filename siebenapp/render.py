from collections import defaultdict


def render_tree(goals):
    graph = goals.all(keys='name,edge,open,select,switchable')
    edges = {key: values['edge'] for key, values in graph.items()}
    layers = min_width(edges, 4)
    for row in sorted(layers.keys()):
        for col, goal_id in enumerate(layers[row]):
            graph[goal_id].update({
                'row': row,
                'col': col,
            })
    return graph


def min_width(source, width):
    unsorted_goals, sorted_goals, goals_on_previous_layers = dict(source), set(), set()
    layers = defaultdict(list)
    current_layer, width_current, width_up = 0, 0, 0
    while unsorted_goals:
        candidates = [(goal, len(edges)) for goal, edges in unsorted_goals.items()
                      if all(v in goals_on_previous_layers for v in edges)]
        for goal, edges in sorted(candidates, key=lambda x: x[1], reverse=True):
            unsorted_goals.pop(goal)
            sorted_goals.add(goal)
            layers[current_layer].append(goal)
            back_edges = len([k for k, vs in source.items() if goal in vs])
            width_current += 1 - edges
            width_up += back_edges
            if (width_current >= width and edges < 1) or (width_up >= width):
                break
        current_layer += 1
        goals_on_previous_layers.update(sorted_goals)
        width_current, width_up = width_up, 0
    return dict(layers)
