"""Deck with shuffle, deal, and burn operations."""

import random
from engine.card import Card, Rank, Suit


class Deck:
    """Standard 52-card deck. Shuffled on creation."""

    def __init__(self, seed: int | None = None):
        self._cards: list[Card] = [
            Card(rank=r, suit=s)
            for s in Suit
            for r in Rank
        ]
        self._rng = random.Random(seed)
        self._rng.shuffle(self._cards)

    def deal(self, n: int = 1) -> list[Card]:
        """Deal n cards from the top of the deck."""
        if n > len(self._cards):
            raise ValueError(f"Cannot deal {n} cards, only {len(self._cards)} remaining")
        dealt = self._cards[:n]
        self._cards = self._cards[n:]
        return dealt

    def burn(self) -> Card:
        """Burn one card (remove from deck). Returns the burned card for history."""
        if not self._cards:
            raise ValueError("Cannot burn, deck is empty")
        return self._cards.pop(0)

    @property
    def remaining(self) -> int:
        return len(self._cards)
