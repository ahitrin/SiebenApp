from unittest import TestCase

from siebenapp.goaltree import Goals
from siebenapp.zoom import Zoom


class TestZoom(TestCase):
    def setUp(self):
        self.goals = Zoom(Goals('Root'))

    def test_single_goal_could_not_be_zoomed(self):
        assert self.goals.all() == {
            1: {'name': 'Root'}
        }
        self.goals.toggle_zoom()
        assert self.goals.all() == {
            1: {'name': 'Root'}
        }

    def test_skip_intermediate_goal_during_zoom(self):
        self.goals.add('Hidden')
        self.goals.add('Zoomed', 2)
        self.goals.select(3)
        assert self.goals.all(keys='name,edge') == {
            1: {'name': 'Root', 'edge': [2]},
            2: {'name': 'Hidden', 'edge': [3]},
            3: {'name': 'Zoomed', 'edge': []},
        }
        self.goals.toggle_zoom()
        assert self.goals.all(keys='name,edge') == {
            -1: {'name': 'Root', 'edge': [3]},
            3: {'name': 'Zoomed', 'edge': []},
        }

    def test_hide_neighbour_goals_during_zoom(self):
        self.goals.add('Zoomed')
        self.goals.add('Hidden 1')
        self.goals.add('Hidden 2')
        self.goals.select(2)
        self.goals.toggle_zoom()
        self.goals.toggle_zoom()
        assert self.goals.all(keys='name,edge') == {
            1: {'name': 'Root', 'edge': [2, 3, 4]},
            2: {'name': 'Zoomed', 'edge': []},
            3: {'name': 'Hidden 1', 'edge': []},
            4: {'name': 'Hidden 2', 'edge': []},
        }

    def test_do_not_hide_subgoals(self):
        self.goals.add('Zoomed')
        self.goals.add('Visible', 2)
        self.goals.select(2)
        self.goals.toggle_zoom()
        assert self.goals.all(keys='name,edge') == {
            -1: {'name': 'Root', 'edge': [2]},
            2: {'name': 'Zoomed', 'edge': [3]},
            3: {'name': 'Visible', 'edge': []},
        }
        self.goals.add('More children', 3)
        assert self.goals.all(keys='name,edge') == {
            -1: {'name': 'Root', 'edge': [2]},
            2: {'name': 'Zoomed', 'edge': [3]},
            3: {'name': 'Visible', 'edge': [4]},
            4: {'name': 'More children', 'edge': []},
        }

    def test_selection_should_not_be_changed_if_selected_goal_is_visible(self):
        self.goals.add('Select root')
        self.goals.add('Previous selected', 2)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.select(2)
        self.goals.toggle_zoom()
        assert self.goals.all(keys='name,select') == {
            -1: {'name': 'Root', 'select': None},
            2: {'name': 'Select root', 'select': 'select'},
            3: {'name': 'Previous selected', 'select': 'prev'},
        }

    def test_selection_should_be_changed_if_selected_goal_is_invisible(self):
        self.goals.add('Previous selected')
        self.goals.add('Zoomed')
        self.goals.select(2)
        self.goals.hold_select()
        self.goals.select(3)
        assert self.goals.events[-1] == ('select', 3)
        self.goals.toggle_zoom()
        assert self.goals.events[-1] == ('hold_select', 3)
