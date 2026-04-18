"""Decision review: compare actions against style guidelines."""

from memory.hand_history import ActionRecord, HandHistory
from strategy.style_profile import StyleProfile


@dataclass
class ActionReview:
    """Review of a single action decision."""
    street: str
    player_id: str
    style: str
    action_taken: str
    hand_strength: float
    was_style_consistent: bool
    deviation_description: str | None
    suggested_action: str | None
    suggestion_reason: str | None


@dataclass
class HandAnalysis:
    """Complete analysis of a hand."""
    hand_id: str
    action_reviews: list[ActionReview]
    overall_notes: list[str]
    style_deviation_count: dict[str, int]


from dataclasses import dataclass
