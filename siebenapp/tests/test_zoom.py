from siebenapp.goaltree import Goals, Edge
from siebenapp.tests.dsl import build_goaltree, open_, selected, previous
from siebenapp.zoom import Zoom


def test_single_goal_could_not_be_zoomed():
    goals = Zoom(Goals('Root'))
    assert goals.q() == {
        1: {'name': 'Root'}
    }
    goals.toggle_zoom()
    assert goals.q() == {
        1: {'name': 'Root'}
    }


def test_skip_intermediate_goal_during_zoom():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Hidden', [3]),
        open_(3, 'Zoomed', select=selected)
    ))
    goals.toggle_zoom()
    assert goals.q(keys='name,edge') == {
        -1: {'name': 'Root', 'edge': [(3, Edge.TYPE_SOFT)]},
        3: {'name': 'Zoomed', 'edge': []},
    }


def test_hide_neighbour_goals_during_zoom():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2, 3, 4]),
        open_(2, 'Zoomed', select=selected),
        open_(3, 'Hidden 1'),
        open_(4, 'Hidden 2')
    ))
    goals.toggle_zoom()
    assert goals.q(keys='name,edge') == {
        -1: {'name': 'Root', 'edge': [(2, Edge.TYPE_SOFT)]},
        2: {'name': 'Zoomed', 'edge': []},
    }


def test_do_not_hide_subgoals():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Zoomed', [3], select=selected),
        open_(3, 'Visible')
    ))
    goals.toggle_zoom()
    assert goals.q(keys='name,edge') == {
        -1: {'name': 'Root', 'edge': [(2, Edge.TYPE_SOFT)]},
        2: {'name': 'Zoomed', 'edge': [(3, Edge.TYPE_STRONG)]},
        3: {'name': 'Visible', 'edge': []},
    }
    goals.add('More children', 3)
    assert goals.q(keys='name,edge') == {
        -1: {'name': 'Root', 'edge': [(2, Edge.TYPE_SOFT)]},
        2: {'name': 'Zoomed', 'edge': [(3, Edge.TYPE_STRONG)]},
        3: {'name': 'Visible', 'edge': [(4, Edge.TYPE_STRONG)]},
        4: {'name': 'More children', 'edge': []},
    }


def test_double_zoom_means_unzoom():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2, 3]),
        open_(2, 'Zoomed', select=selected),
        open_(3, 'Hidden')
    ))
    goals.toggle_zoom()
    assert goals.q() == {
        -1: {'name': 'Root'},
        2: {'name': 'Zoomed'},
    }
    goals.toggle_zoom()
    assert goals.q('name,edge') == {
        1: {'name': 'Root', 'edge': [(2, Edge.TYPE_STRONG), (3, Edge.TYPE_STRONG)]},
        2: {'name': 'Zoomed', 'edge': []},
        3: {'name': 'Hidden', 'edge': []},
    }


def test_stacked_zoom():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Skip me', [3]),
        open_(3, 'Intermediate zoom', [4], select=selected),
        open_(4, 'Next zoom', [5]),
        open_(5, 'Top')
    ))
    goals.toggle_zoom()
    goals.select(4)
    goals.toggle_zoom()
    assert set(goals.q().keys()) == {-1, 4, 5}
    goals.toggle_zoom()
    # Zoom on goal 3 still exists
    assert set(goals.q().keys()) == {-1, 3, 4, 5}


def test_selection_should_not_be_changed_if_selected_goal_is_visible():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Select root', [3], select=selected),
        open_(3, 'Previous selected', select=previous)
    ))
    goals.toggle_zoom()
    assert goals.q(keys='name,select') == {
        -1: {'name': 'Root', 'select': None},
        2: {'name': 'Select root', 'select': 'select'},
        3: {'name': 'Previous selected', 'select': 'prev'},
    }


def test_selection_should_be_changed_if_selected_goal_is_invisible():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2, 3]),
        open_(2, 'Previous selected', select=previous),
        open_(3, 'Zoomed', select=selected)
    ))
    goals.toggle_zoom()
    assert goals.events[-1] == ('hold_select', 3)


def test_closing_zoom_root_should_cause_unzoom():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Intermediate', [3]),
        open_(3, 'Zoom here', select=selected)
    ))
    goals.toggle_zoom()
    goals.toggle_close()
    assert goals.q(keys='name,select,open') == {
        1: {'name': 'Root', 'select': 'select', 'open': True},
        2: {'name': 'Intermediate', 'select': None, 'open': True},
        3: {'name': 'Zoom here', 'select': None, 'open': False},
    }


def test_goal_closing_must_not_cause_root_selection():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Zoom root', [3], select=selected),
        open_(3, 'Close me')
    ))
    goals.toggle_zoom()
    assert goals.q(keys='name,select,open') == {
        -1: {'name': 'Root', 'select': None, 'open': True},
        2: {'name': 'Zoom root', 'select': 'select', 'open': True},
        3: {'name': 'Close me', 'select': None, 'open': True},
    }
    goals.select(3)
    goals.toggle_close()
    assert goals.q(keys='name,select,open') == {
        -1: {'name': 'Root', 'select': None, 'open': True},
        2: {'name': 'Zoom root', 'select': 'select', 'open': True},
        3: {'name': 'Close me', 'select': None, 'open': False},
    }


def test_goal_reopening_must_not_change_selection():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Zoom root', [3], select=selected),
        open_(3, 'Reopen me')
    ))
    goals.toggle_zoom()
    goals.select(3)
    goals.toggle_close()
    assert goals.q(keys='name,select,open') == {
        -1: {'name': 'Root', 'select': None, 'open': True},
        2: {'name': 'Zoom root', 'select': 'select', 'open': True},
        3: {'name': 'Reopen me', 'select': None, 'open': False},
    }
    goals.select(3)
    goals.toggle_close()
    assert goals.q(keys='name,select,open') == {
        -1: {'name': 'Root', 'select': None, 'open': True},
        2: {'name': 'Zoom root', 'select': 'prev', 'open': True},
        3: {'name': 'Reopen me', 'select': 'select', 'open': True},
    }


def test_deleting_zoom_root_should_cause_unzoom():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Intermediate', [3]),
        open_(3, 'Zoom here', select=selected)
    ))
    goals.toggle_zoom()
    goals.delete()
    assert goals.q(keys='name,select,open') == {
        1: {'name': 'Root', 'select': 'select', 'open': True},
        2: {'name': 'Intermediate', 'select': None, 'open': True},
    }


def test_goal_deletion_must_not_cause_root_selection():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'Hidden', [3]),
        open_(3, 'Zoom root', [4], select=selected),
        open_(4, 'Deleted')
    ))
    goals.toggle_zoom()
    assert goals.q(keys='name,select') == {
        -1: {'name': 'Root', 'select': None},
        3: {'name': 'Zoom root', 'select': 'select'},
        4: {'name': 'Deleted', 'select': None},
    }
    goals.select(4)
    goals.delete()
    assert goals.q(keys='name,select') == {
        -1: {'name': 'Root', 'select': None},
        3: {'name': 'Zoom root', 'select': 'select'},
    }


def test_zoom_events():
    goals = Zoom(build_goaltree(
        open_(1, 'Root', [2]),
        open_(2, 'First zoom', [3], select=selected),
        open_(3, 'Intermediate', [4]),
        open_(4, 'Second zoom', [5]),
        open_(5, 'Top')
    ))
    goals.toggle_zoom()
    assert goals.events[-1] == ('zoom', 2, 2)
    goals.select(4)
    goals.hold_select()
    goals.toggle_zoom()
    assert goals.events[-1] == ('zoom', 3, 4)
    goals.toggle_zoom()
    assert goals.events[-1] == ('unzoom', 4)
