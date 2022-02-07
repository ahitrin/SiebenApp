from siebenapp.domain import Graph
from siebenapp.filter_view import FilterView
from siebenapp.open_view import OpenView
from siebenapp.progress_view import ProgressView
from siebenapp.switchable_view import SwitchableView


def wrap_with_views(graph: Graph) -> Graph:
    return FilterView(SwitchableView(OpenView(ProgressView(graph))))
