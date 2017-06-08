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
        assert self.goals.all(keys='name,edge') == {
            -1: {'name': 'Root', 'edge': [2]},
            2: {'name': 'Zoomed', 'edge': []},
        }

    def test_double_zoom_means_unzoom(self):
        self.goals.add('Zoomed')
        self.goals.add("Hidden")
        self.goals.select(2)
        self.goals.toggle_zoom()
        assert self.goals.all() == {
            -1: {'name': 'Root'},
            2: {'name': 'Zoomed'},
        }
        self.goals.toggle_zoom()
        assert self.goals.all('name,edge') == {
            1: {'name': 'Root', 'edge': [2, 3]},
            2: {'name': 'Zoomed', 'edge': []},
            3: {'name': 'Hidden', 'edge': []},
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

    def test_zoom_events(self):
        self.goals.add('Intermediate')
        self.goals.add('Zoom here', 2)
        self.goals.toggle_zoom()
        assert all(e[0] != 'select' for e in self.goals.events)
        self.goals.select(3)
        self.goals.hold_select()
        self.goals.toggle_zoom()
        assert self.goals.events[-1] == ('zoom', 3)
        self.goals.toggle_zoom()
        assert self.goals.events[-1] == ('zoom', 1)

    def test_goal_closing_must_not_cause_root_selection(self):
        self.goals.add('Zoom root')
        self.goals.add('Close me', 2)
        self.goals.select(2)
        self.goals.toggle_zoom()
        assert self.goals.all(keys='name,select,open') == {
            -1: {'name': 'Root', 'select': None, 'open': True},
            2: {'name': 'Zoom root', 'select': 'select', 'open': True},
            3: {'name': 'Close me', 'select': None, 'open': True},
        }
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='name,select,open') == {
            -1: {'name': 'Root', 'select': None, 'open': True},
            2: {'name': 'Zoom root', 'select': 'select', 'open': True},
            3: {'name': 'Close me', 'select': None, 'open': False},
        }

    def test_goal_reopening_must_not_change_selection(self):
        self.goals.add('Zoom root')
        self.goals.add('Reopen me', 2)
        self.goals.select(2)
        self.goals.toggle_zoom()
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='name,select,open') == {
            -1: {'name': 'Root', 'select': None, 'open': True},
            2: {'name': 'Zoom root', 'select': 'select', 'open': True},
            3: {'name': 'Reopen me', 'select': None, 'open': False},
        }
        self.goals.select(3)
        self.goals.toggle_close()
        assert self.goals.all(keys='name,select,open') == {
            -1: {'name': 'Root', 'select': None, 'open': True},
            2: {'name': 'Zoom root', 'select': 'prev', 'open': True},
            3: {'name': 'Reopen me', 'select': 'select', 'open': True},
        }

    def test_goal_deletion_must_not_cause_root_selection(self):
        self.goals.add('Hidden')
        self.goals.add('Zoom root', 2)
        self.goals.add('Deleted', 3)
        self.goals.select(3)
        self.goals.toggle_zoom()
        assert self.goals.all(keys='name,select') == {
            -1: {'name': 'Root', 'select': None},
            3: {'name': 'Zoom root', 'select': 'select'},
            4: {'name': 'Deleted', 'select': None},
        }
        self.goals.select(4)
        self.goals.delete()
        assert self.goals.all(keys='name,select') == {
            -1: {'name': 'Root', 'select': None},
            3: {'name': 'Zoom root', 'select': 'select'},
        }
