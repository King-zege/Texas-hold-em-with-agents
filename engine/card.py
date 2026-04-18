"""Card representation with Unicode suit display."""

from enum import Enum
from dataclasses import dataclass


class Suit(Enum):
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"


# Unicode symbols for display
_SUIT_SYMBOLS = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}


class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


# Display mapping for rank values
_RANK_DISPLAY = {
    "2": "2", "3": "3", "4": "4", "5": "5", "6": "6",
    "7": "7", "8": "8", "9": "9", "T": "10", "J": "J",
    "Q": "Q", "K": "K", "A": "A",
}


@dataclass(frozen=True)
class Card:
    """Immutable playing card with Unicode display support."""
    rank: Rank
    suit: Suit

    @classmethod
    def from_str(cls, s: str) -> "Card":
        """Parse string like 'Ah', 'Tc', '2s' into a Card."""
        return cls(rank=Rank(s[0]), suit=Suit(s[1]))

    def to_treys_str(self) -> str:
        """Convert to treys-compatible string like 'Ah'."""
        return f"{self.rank.value}{self.suit.value}"

    def to_treys_int(self) -> int:
        """Convert to treys integer for hand evaluation."""
        from treys import Card as TreysCard
        return TreysCard.new(self.to_treys_str())

    def __str__(self) -> str:
        """Unicode display: A♥, K♠, 10♣, etc."""
        rank_display = _RANK_DISPLAY[self.rank.value]
        suit_symbol = _SUIT_SYMBOLS[self.suit.value]
        return f"{rank_display}{suit_symbol}"

    def __repr__(self) -> str:
        return f"Card({self.rank.name}, {self.suit.name})"
