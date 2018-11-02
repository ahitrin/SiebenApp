# pylint: disable=too-few-public-methods
from typing import Dict, Any


class Graph:
    """Base interface definition"""

    def q(self, keys: str = 'name') -> Dict[int, Any]:
        """Run search query against goaltree state"""
        raise NotImplementedError
