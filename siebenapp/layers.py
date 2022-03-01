from typing import Optional

from siebenapp.autolink import AutoLink
from siebenapp.domain import Graph
from siebenapp.filter_view import FilterView
from siebenapp.goaltree import Goals
from siebenapp.open_view import OpenView
from siebenapp.progress_view import ProgressView
from siebenapp.switchable_view import SwitchableView
from siebenapp.zoom import Zoom, ZoomData


def persistent_layers(graph: Goals, zoom_data: Optional[ZoomData] = None) -> Graph:
    """Wrap given graph with all standard persistent logic layers"""
    return Zoom(AutoLink(graph), zoom_data)


def view_layers(graph: Graph) -> Graph:
    """Wrap given graph with all standard non-persistent (view) logic layers"""
    return FilterView(SwitchableView(OpenView(ProgressView(graph))))


def all_layers(graph: Goals, zoom_data: Optional[ZoomData] = None) -> Graph:
    """Wrap given Goals instance with all default logic layers"""
    return view_layers(persistent_layers(graph, zoom_data))


def get_root(graph: Graph) -> Goals:
    """Find the deepest layer that contains goaltree data"""
    max_reasonable_depth: int = 10
    for _ in range(max_reasonable_depth):
        if isinstance(graph, Goals):
            return graph
        graph = graph.goaltree
    raise Exception(f"Cannot find root layer after {max_reasonable_depth} attempts")
