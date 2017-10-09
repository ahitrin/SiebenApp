from collections import defaultdict


def render_tree(goals, render_log):
    edges = {key: values['edge'] for key, values in goals.all(keys='edge').items()}
    render_log.append("Total goals: %d" % len(edges))
    layers = longest_path(edges)
    for l in sorted(layers.keys()):
        render_log.append('Layer %s -> %s' % (l, layers[l]))


def longest_path(source):
    layers = defaultdict(list)
    current_layer = 1
    layered = set()
    allowed_targets = set()
    edges = set(source.keys())

    while layered != edges:
        candidates = {k for k in edges.difference(layered)
                      if all(e in allowed_targets for e in source[k])}
        if candidates:
            next_candidate = candidates.pop()
            layers[current_layer].append(next_candidate)
            layered.add(next_candidate)
        else:
            current_layer += 1
            allowed_targets.update(layered)
    return dict(layers)
