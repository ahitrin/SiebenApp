class Zoom:
    override = ['_build_visible_goals', 'q', 'delete', 'export', 'goaltree',
                'toggle_close', 'toggle_zoom', 'zoom_root']

    def __init__(self, goaltree):
        self.goaltree = goaltree
        self.zoom_root = [1]

    def toggle_zoom(self):
        selection = self.settings['selection']
        if selection == self.zoom_root[-1] and len(self.zoom_root) > 1:
            # unzoom
            last_zoom = self.zoom_root.pop(-1)
            self.events.append(('zoom', last_zoom))
            return
        if selection not in self.zoom_root:
            self.zoom_root.append(selection)
            self.events.append(('zoom', selection))
            visible_goals = self._build_visible_goals()
            if self.settings['previous_selection'] not in visible_goals:
                self.goaltree.hold_select()

    def q(self, keys='name'):
        origin_goals = self.goaltree.q(keys)
        if self.zoom_root == [1]:
            return origin_goals
        visible_goals = self._build_visible_goals()
        zoomed_goals = {k: v for k, v in origin_goals.items()
                        if k in visible_goals}
        zoomed_goals[-1] = origin_goals[1]
        if 'edge' in keys:
            zoomed_goals[-1]['edge'] = [self.zoom_root[-1]]
        return zoomed_goals

    def toggle_close(self):
        if self.settings['selection'] == self.zoom_root[-1]:
            self.toggle_zoom()
        self.goaltree.toggle_close()
        if self.settings['selection'] not in self._build_visible_goals():
            self.goaltree.select(self.zoom_root[-1])
            self.goaltree.hold_select()

    def delete(self, goal_id=0):
        if self.settings['selection'] == self.zoom_root[-1]:
            self.toggle_zoom()
        self.goaltree.delete(goal_id)
        if self.settings['selection'] != self.zoom_root[-1]:
            self.goaltree.select(self.zoom_root[-1])
            self.goaltree.hold_select()

    def _build_visible_goals(self):
        edges = self.goaltree.q('edge')
        current_zoom_root = self.zoom_root[-1]
        visible_goals = {current_zoom_root}
        goals_to_visit = set(edges[current_zoom_root]['edge'])
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

    @staticmethod
    def build(goals, data):
        result = Zoom(goals)
        result.zoom_root = [x[1] for x in data] if data else [1]
        return result

    @staticmethod
    def export(goals):
        return [(1, getattr(goals, 'zoom_root', 1))]
