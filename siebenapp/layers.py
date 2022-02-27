from siebenapp.domain import Graph
from siebenapp.filter_view import FilterView
from siebenapp.open_view import OpenView
from siebenapp.progress_view import ProgressView
from siebenapp.switchable_view import SwitchableView


def view_layers(graph: Graph) -> Graph:
    """Wrap given graph with all standard non-persistent (view) logic layers"""
    return FilterView(SwitchableView(OpenView(ProgressView(graph))))
