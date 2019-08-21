from typing import Dict

from siebenapp.goaltree import Goals


def complexity(goals: Goals) -> Dict[str, int]:
    goals_count = len(goals.goals)
    edges_count = len(goals.edges)
    paths_count = {1: 0}
    to_visit = goals._forward_edges(1)
    while to_visit:
        free_goals = [g for g in to_visit
                      if all(p in paths_count for p in goals._back_edges(g))]
        assert free_goals
        next_goal = free_goals[0]
        to_visit.remove(next_goal)
        paths_count[next_goal] = max(1, sum(paths_count[p] for p in goals._back_edges(next_goal)))
    return {
        'goals': goals_count,
        'edges': edges_count,
        'paths': sum(paths_count.values()),
    }
