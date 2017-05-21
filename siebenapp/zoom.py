class Zoom:
    override = ['goals', 'zoom_root', 'toggle_zoom', 'all',
                '_build_visible_goals']

    def __init__(self, goaltree):
        self.goals = goaltree
        self.zoom_root = 1

    def toggle_zoom(self):
        selection = self.goals.selection
        if selection == self.zoom_root:
            self.zoom_root = 1
            return
        self.zoom_root = selection
        visible_goals = self._build_visible_goals()
        prev_selection = self.goals.previous_selection
        if prev_selection not in visible_goals:
            self.goals.hold_select()

    def all(self, keys='name'):
        origin_goals = self.goals.all(keys)
        if self.zoom_root == 1:
            return origin_goals
        visible_goals = self._build_visible_goals()
        zoomed_goals = {k: v for k, v in origin_goals.items()
                        if k in visible_goals}
        zoomed_goals[-1] = origin_goals[1]
        if 'edge' in keys:
            zoomed_goals[-1]['edge'] = [self.zoom_root]
        return zoomed_goals

    def _build_visible_goals(self):
        edges = self.goals.all('edge')
        visible_goals = {self.zoom_root}
        goals_to_visit = set(edges[self.zoom_root]['edge'])
        while goals_to_visit:
            next_child = goals_to_visit.pop()
            visible_goals.add(next_child)
            goals_to_visit.update(edges[next_child]['edge'])
        return visible_goals

    def __getattribute__(self, item):
        override = object.__getattribute__(self, 'override')
        goals = object.__getattribute__(self, 'goals')
        if item in override:
            return object.__getattribute__(self, item)
        return getattr(goals, item)