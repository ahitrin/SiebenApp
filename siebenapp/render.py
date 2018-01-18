from collections import defaultdict


def render_tree(goals):
    graph = goals.all(keys='name,edge,open,select,switchable')
    edges = {key: values['edge'] for key, values in graph.items()}
    layers = min_width(edges, 4)
    for row in sorted(layers.keys()):
        for col, goal_id in enumerate(layers[row]):
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
                'edge': edges[goal_id],
            })
    return graph


# pylint: disable=too-many-locals
def min_width(source, width):
    unsorted_goals, sorted_goals, goals_on_previous_layers = dict(source), set(), set()
    layers = defaultdict(list)
    current_layer, width_current, width_up = 0, 0, 0
    incoming_edges, outgoing_edges = set(), set()
    while unsorted_goals:
        candidates = [(goal, edges) for goal, edges in unsorted_goals.items()
                      if all(v in goals_on_previous_layers for v in edges)]
        for goal, edges in sorted(candidates, key=lambda x: len(x[1]), reverse=True):
            unsorted_goals.pop(goal)
            sorted_goals.add(goal)
            try:
                incoming_edges.remove(goal)
            except KeyError:
                pass
            layers[current_layer].append(goal)
            back_edges = [k for k, vs in source.items() if goal in vs]
            outgoing_edges.update(e for e in back_edges)
            width_current += 1 - len(edges)
            width_up += len(back_edges)
            if (width_current >= width and len(edges) < 1) or (width_up >= width):
                break
        for original_id in incoming_edges:
            new_goal_name = '%d_%d' % (original_id, current_layer)
            source[new_goal_name] = [g for g in source[original_id]
                                     if g in sorted_goals and g not in layers[current_layer]]
            for g in source[new_goal_name]:
                source[original_id].remove(g)
            source[original_id].append(new_goal_name)
            layers[current_layer].append(new_goal_name)
            sorted_goals.add(new_goal_name)
        current_layer += 1
        goals_on_previous_layers.update(sorted_goals)
        width_current, width_up = width_up, 0
        incoming_edges.update(outgoing_edges)
        outgoing_edges.clear()
    return dict(layers)
