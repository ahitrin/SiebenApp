from dataclasses import replace, dataclass
from typing import Any

from siebenapp.domain import (
    Graph,
    Rename,
    ToggleClose,
    ToggleLink,
    Insert,
    Delete,
    Command,
    RenderResult,
)


SelectableData = list[tuple[str, int]]

OPTION_SELECT = "select"
OPTION_PREV_SELECT = "prev_select"


@dataclass(frozen=True)
class Select(Command):
    """Select a goal by its id whether it exist. Do nothing in other case"""

    goal_id: int


@dataclass(frozen=True)
class HoldSelect(Command):
    """Saves current selection into the "previous selection" state"""

    goal_id: int = 0


class Selectable(Graph):
    def __init__(self, goals: Graph, data: SelectableData | None = None):
        super().__init__(goals)
        selection_dict: dict[str, int] = dict(data or [])
        original_root = int(list(goals.q().roots)[0])
        self.selection: int = selection_dict.get("selection", original_root)
        self.previous_selection: int = selection_dict.get(
            "previous_selection", original_root
        )

    def accept_Select(self, command: Select):
        goal_id: int = command.goal_id
        if self.goaltree.has_goal(goal_id):
            self.selection = goal_id
            self._events.append(("select", goal_id))

    def accept_HoldSelect(self, command: HoldSelect):
        self.previous_selection = self.selection
        self._events.append(("hold_select", self.selection))

    def accept_Rename(self, command: Rename) -> None:
        target = command.goal_id or self.selection
        self.goaltree.accept(replace(command, goal_id=target))

    def accept_ToggleClose(self, command: ToggleClose) -> None:
        target = command.goal_id or self.selection
        if self._command_approved(replace(command, goal_id=target)):
            # Change selection only when goal was successfully closed
            if self.goaltree.is_closed(self.selection):
                if self.previous_selection != self.selection:
                    self.accept_Select(Select(self.previous_selection))
                else:
                    next_selection = self._first_open_and_switchable(command.root)
                    self.accept_Select(Select(next_selection))
                    self.accept_HoldSelect(HoldSelect())

    def accept_ToggleLink(self, command: ToggleLink) -> None:
        lower = command.lower or self.previous_selection
        upper = command.upper or self.selection
        self.goaltree.accept(replace(command, lower=lower, upper=upper))

    def accept_Insert(self, command: Insert) -> None:
        lower = command.lower or self.previous_selection
        upper = command.upper or self.selection
        self.goaltree.accept(replace(command, lower=lower, upper=upper))

    def accept_Delete(self, command: Delete) -> None:
        target = command.goal_id or self.selection
        parent: int = self.goaltree.parent(target)
        if self._command_approved(replace(command, goal_id=target)):
            self.accept_Select(Select(parent))
            self.accept_HoldSelect(HoldSelect())

    def _command_approved(self, command: Command) -> bool:
        events_before: int = len(self.events())
        self.goaltree.accept(command)
        events_after: int = len(self.events())
        return events_after > events_before

    def q(self) -> RenderResult:
        rr = self.goaltree.q()
        return replace(
            rr,
            global_opts=rr.global_opts
            | {
                OPTION_SELECT: self.selection,
                OPTION_PREV_SELECT: self.previous_selection,
            },
        )

    def settings(self, key: str) -> Any:
        selection_settings = {
            "selection": self.selection,
            "previous_selection": self.previous_selection,
        }
        if key in selection_settings:
            return selection_settings.get(key)

        return self.goaltree.settings(key)

    @staticmethod
    def export(goals: "Selectable") -> SelectableData:
        return [
            ("selection", goals.selection),
            ("previous_selection", goals.previous_selection),
        ]
