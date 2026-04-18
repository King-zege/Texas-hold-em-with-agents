"""Postflop hand strength evaluation with draw detection."""

from engine.card import Card, Suit, Rank
from engine.hand_evaluator import HandEvaluator


def has_flush_draw(cards: list[Card], community: list[Card]) -> bool:
    """Check if player has a flush draw."""
    all_cards = cards + community
    suit_counts = {}
    for c in all_cards:
        suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1

    # Flush draw = 4 cards of same suit
    return any(count == 4 for count in suit_counts.values())


def has_straight_draw(cards: list[Card], community: list[Card]) -> bool:
    """Check if player has a straight draw (OESD or gutshot)."""
    if len(community) < 3:
        return False

    all_cards = cards + community
    rank_values = [c.rank.value for c in all_cards]

    # Convert to numeric values
    value_map = {"A": 14, "K": 13, "Q": 12, "J": 11,
                 "T": 10, "9": 9, "8": 8, "7": 7,
                 "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}
    nums = [value_map.get(v, 0) for v in rank_values]

    # Check for 4 consecutive cards (OESD)
    unique = sorted(list(set(nums)))
    for i in range(len(unique) - 3):
        if unique[i+3] - unique[i] == 3:
            return True  # Open-ended straight draw

    # Check for gutshot (one gap)
    for i in range(len(unique) - 4):
        # Need 5 consecutive cards with exactly one gap
        gap_count = 0
        for j in range(4):
            if unique[i+j+1] - unique[i+j] > 1:
                gap_count += 1
            if gap_count > 1:
                break
        if gap_count == 1:
            return True  # Gutshot straight draw

    return False


def postflop_hand_strength(
    cards: list[Card],
    community: list[Card],
) -> float:
    """
    Returns 0.0-1.0 postflop hand strength.

    Uses treys evaluator and adds draw bonuses.
    """
    if not community:
        # No community cards yet - use rough estimate
        # This shouldn't happen postflop, but handle gracefully
        return 0.5

    evaluator = HandEvaluator()
    rank = evaluator.evaluate(cards, community)
    strength = evaluator.hand_strength_pct(cards, community)

    # Draw bonuses
    draw_bonus = 0.0

    if has_flush_draw(cards, community):
        draw_bonus += 0.15

    if has_straight_draw(cards, community):
        # Smaller bonus for gutshot vs OESD, but we use average
        draw_bonus += 0.10

    # Don't exceed 1.0
    return min(1.0, strength + draw_bonus)
