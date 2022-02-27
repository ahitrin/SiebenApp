from typing import Optional

from siebenapp.domain import Graph
from siebenapp.filter_view import FilterView
from siebenapp.goaltree import Goals
from siebenapp.open_view import OpenView
from siebenapp.progress_view import ProgressView
from siebenapp.switchable_view import SwitchableView
from siebenapp.zoom import Zoom, ZoomData


def persistent_layers(graph: Goals, zoom_data: Optional[ZoomData] = None) -> Graph:
    """Wrap given graph with all standard persistent logic layers"""
    return Zoom(graph, zoom_data)


def view_layers(graph: Graph) -> Graph:
    """Wrap given graph with all standard non-persistent (view) logic layers"""
    return FilterView(SwitchableView(OpenView(ProgressView(graph))))
