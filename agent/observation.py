"""Observation: what an agent is allowed to see when making a decision."""

from dataclasses import dataclass
from engine.card import Card
from engine.action import Action


@dataclass(frozen=True)
class Observation:
    """Everything an agent is allowed to see when making a decision.

    This must NEVER contain other agents' hole cards.
    """
    # Own identity
    player_id: str
    style: str
    hole_cards: list[Card]
    stack_bb: float

    # Position
    seat_index: int
    button_index: int
    num_players: int
    position_name: str  # "UTG", "MP", "CO", "BTN", "SB", "BB"

    # Current street
    street: str  # "preflop", "flop", "turn", "river"
    community_cards: list[Card]

    # Betting state
    pot_bb: float
    current_bet_to_call_bb: float  # Amount needed to call
    min_raise_bb: float
    max_raise_bb: float  # Stack limit

    # Actions this street (by previous players)
    # Each tuple: (player_id, action, position_name, stack_after_bb)
    actions_this_street: list[tuple[str, Action, str, float]]

    # Active opponents count
    active_opponents: int

    # SPR (Stack-to-Pot Ratio)
    spr: float
