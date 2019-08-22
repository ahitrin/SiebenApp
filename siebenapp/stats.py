from typing import Dict, Set

from siebenapp.goaltree import Goals


def complexity(goals: Goals) -> Dict[str, int]:
    def _forward_goals(goal: int) -> Set[int]:
        return set(k[1] for k, v in goals.edges.items() if k[0] == goal)

    def _back_goals(goal: int) -> Set[int]:
        return set(k[0] for k, v in goals.edges.items() if k[1] == goal)

    paths_count = {1: 1}    # type: Dict[int, int]
    to_visit = _forward_goals(1)
    while to_visit:
        possible_goals = [g for g in to_visit
                          if all(p in paths_count for p in _back_goals(g))]
        next_goal = possible_goals[0]
        to_visit.remove(next_goal)
        to_visit = to_visit.union(_forward_goals(next_goal))
        paths_count[next_goal] = sum(paths_count[g] for g in _back_goals(next_goal))
    paths_count.pop(1)
    return {
        'goals': len(goals.goals),
        'edges': len(goals.edges),
        'paths': sum(paths_count.values()),
    }
