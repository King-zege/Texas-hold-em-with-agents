"""Preflop hand classification and strength evaluation."""

from engine.card import Card, Rank, Suit


def classify_preflop_hand(cards: list[Card]) -> str:
    """
    Classify a preflop hand type.

    Returns one of:
    - "premium_pair" (AA, KK)
    - "strong_pair" (QQ, JJ)
    - "medium_pair" (TT, 99, 88, 77)
    - "small_pair" (66-22)
    - "suited_ace_broadway" (AKs, AQs, AJs)
    - "suited_ace_medium" (ATs-A2s)
    - "offsuit_ace_broadway" (AKo, AQo)
    - "suited_broadway" (KQs, KJs, QJs)
    - "offsuit_broadway" (KQo, AJo, KJo)
    - "suited_connector" (89s-54s)
    - "suited_gapper" (97s, 86s, etc.)
    - "offsuit_connector" (89o-54o)
    - "trash" (everything else)
    """
    if len(cards) != 2:
        return "trash"

    c1, c2 = cards
    r1, r2 = c1.rank, c2.rank
    s1, s2 = c1.suit, c2.suit
    is_pocket_pair = r1 == r2
    is_suited = s1 == s2

    # Sort ranks for easier comparison
    ranks = sorted([r1, r2], key=lambda r: r.value)

    if is_pocket_pair:
        if ranks[0] == Rank.ACE or ranks[0] == Rank.KING:
            return "premium_pair"
        elif ranks[0] in (Rank.QUEEN, Rank.JACK):
            return "strong_pair"
        elif ranks[0] in (Rank.TEN, Rank.NINE, Rank.EIGHT, Rank.SEVEN):
            return "medium_pair"
        else:
            return "small_pair"

    # Ace hands
    if Rank.ACE in ranks:
        if is_suited:
            if Rank.KING in ranks or Rank.QUEEN in ranks or Rank.JACK in ranks:
                return "suited_ace_broadway"
            else:
                return "suited_ace_medium"
        else:
            if Rank.KING in ranks or Rank.QUEEN in ranks:
                return "offsuit_ace_broadway"
            else:
                return "trash"

    # Broadway (T through A) hands
    is_broadway = all(r.value in "AKQJT" for r in ranks)

    if is_broadway:
        if is_suited:
            return "suited_broadway"
        else:
            return "offsuit_broadway"

    # Check for connectors (consecutive ranks)
    rank_values = [r.value for r in ranks]
    connector_gap = abs(ord(rank_values[1]) - ord(rank_values[0]))

    if connector_gap == 1:
        if is_suited:
            return "suited_connector"
        else:
            return "offsuit_connector"
    elif connector_gap == 2:
        if is_suited:
            return "suited_gapper"
        else:
            return "offsuit_connector"

    return "trash"


# Base strength for each hand class (before position adjustment)
_HAND_CLASS_STRENGTH = {
    "premium_pair": 0.95,
    "strong_pair": 0.88,
    "medium_pair": 0.75,
    "small_pair": 0.60,
    "suited_ace_broadway": 0.85,
    "suited_ace_medium": 0.62,
    "offsuit_ace_broadway": 0.78,
    "suited_broadway": 0.72,
    "offsuit_broadway": 0.60,
    "suited_connector": 0.55,
    "suited_gapper": 0.48,
    "offsuit_connector": 0.35,
    "offsuit_gapper": 0.28,
    "trash": 0.20,
}

# Position strength multipliers (earlier positions = more conservative)
_POSITION_STRENGTH = {
    "UTG": 0.70,
    "UTG+1": 0.73,
    "MP": 0.76,
    "LJ": 0.80,
    "HJ": 0.84,
    "CO": 0.88,
    "BTN": 0.93,
    "SB": 0.85,
    "BB": 0.87,
}


def preflop_hand_strength(cards: list[Card], position: str, num_players: int = 6) -> float:
    """
    Returns 0.0-1.0 preflop hand strength.

    Adjusts base strength by position and number of players.
    """
    hand_class = classify_preflop_hand(cards)
    base_strength = _HAND_CLASS_STRENGTH.get(hand_class, 0.20)

    # Position adjustment
    pos_mult = _POSITION_STRENGTH.get(position, 0.80)

    # For very tight positions (UTG in full ring), be more conservative
    if num_players >= 9 and position in ("UTG", "UTG+1"):
        pos_mult *= 0.9

    # Calculate final strength with slight randomness for variety
    strength = min(1.0, base_strength * pos_mult + 0.05)

    return strength
