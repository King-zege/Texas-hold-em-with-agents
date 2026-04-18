"""Action types and Action dataclass for poker decisions."""

from enum import Enum
from dataclasses import dataclass


class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True)
class Action:
    """A poker action. Amount is in BB units for BET/RAISE/ALL_IN."""
    type: ActionType
    amount: float = 0.0

    def __str__(self) -> str:
        if self.type in (ActionType.BET, ActionType.RAISE, ActionType.ALL_IN) and self.amount > 0:
            return f"{self.type.value} {self.amount}BB"
        return self.type.value

    @property
    def is_aggressive(self) -> bool:
        return self.type in (ActionType.BET, ActionType.RAISE, ActionType.ALL_IN)
