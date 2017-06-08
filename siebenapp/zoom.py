class Zoom:
    override = ['_build_visible_goals', 'all', 'delete', 'goaltree',
                'toggle_close', 'toggle_zoom', 'zoom_root']

    def __init__(self, goaltree):
        self.goaltree = goaltree
        self.zoom_root = 1

    def toggle_zoom(self):
        selection = self.goaltree.selection
        if selection == self.zoom_root:
            self.zoom_root = 1
            self.events.append(('zoom', self.zoom_root))
            return
        self.zoom_root = selection
        visible_goals = self._build_visible_goals()
        prev_selection = self.goaltree.previous_selection
        self.events.append(('zoom', self.zoom_root))
        if prev_selection not in visible_goals:
            self.goaltree.hold_select()

    def all(self, keys='name'):
        origin_goals = self.goaltree.all(keys)
        if self.zoom_root == 1:
            return origin_goals
        visible_goals = self._build_visible_goals()
        zoomed_goals = {k: v for k, v in origin_goals.items()
                        if k in visible_goals}
        zoomed_goals[-1] = origin_goals[1]
        if 'edge' in keys:
            zoomed_goals[-1]['edge'] = [self.zoom_root]
        return zoomed_goals

    def toggle_close(self):
        self.goaltree.toggle_close()
        if self.goaltree.selection not in self._build_visible_goals():
            self.goaltree.select(self.zoom_root)
            self.goaltree.hold_select()

    def delete(self, goal_id=0):
        self.goaltree.delete(goal_id)
        if self.goaltree.selection != self.zoom_root:
            self.goaltree.select(self.zoom_root)
            self.goaltree.hold_select()

    def _build_visible_goals(self):
        edges = self.goaltree.all('edge')
        visible_goals = {self.zoom_root}
        goals_to_visit = set(edges[self.zoom_root]['edge'])
        while goals_to_visit:
            next_child = goals_to_visit.pop()
            visible_goals.add(next_child)
            goals_to_visit.update(edges[next_child]['edge'])
        return visible_goals

    def __getattribute__(self, item):
        override = object.__getattribute__(self, 'override')
        goals = object.__getattribute__(self, 'goaltree')
        if item in override:
            return object.__getattribute__(self, item)
        return getattr(goals, item)
