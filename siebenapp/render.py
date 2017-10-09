def render_tree(goals, render_log):
    data = goals.all(keys='edge')
    for k in sorted(data.keys()):
        render_log.append('%s -> %s' % (str(k), str(data[k]['edge'])))
    render_log.append("Total goals: %d" % len(data))
