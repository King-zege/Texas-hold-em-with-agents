"""Hand evaluation wrapper around treys library."""

from engine.card import Card


class HandEvaluator:
    """Wraps treys.Evaluator with our Card representation."""

    def __init__(self):
        from treys import Evaluator
        self._evaluator = Evaluator()

    def evaluate(self, hole_cards: list[Card], community_cards: list[Card]) -> int:
        """Returns treys rank integer. Lower = stronger hand."""
        from treys import Card as TreysCard
        treys_hole = [TreysCard.new(c.to_treys_str()) for c in hole_cards]
        treys_board = [TreysCard.new(c.to_treys_str()) for c in community_cards]
        return self._evaluator.evaluate(treys_board, treys_hole)

    def rank_class(self, rank: int) -> int:
        """Returns 1-9 hand class (1=Straight Flush, 9=High Card)."""
        return self._evaluator.get_rank_class(rank)

    def rank_name(self, rank: int) -> str:
        """Returns Chinese-readable hand name."""
        NAMES = {
            1: "同花顺", 2: "四条", 3: "葫芦", 4: "同花",
            5: "顺子", 6: "三条", 7: "两对", 8: "一对", 9: "高牌",
        }
        rc = self.rank_class(rank)
        return NAMES.get(rc, f"Unknown({rc})")

    def rank_name_en(self, rank: int) -> str:
        """Returns English hand name."""
        return self._evaluator.class_to_string(self._evaluator.get_rank_class(rank))

    def compare(self, rank1: int, rank2: int) -> int:
        """Returns -1 if rank1 wins, 1 if rank2 wins, 0 if tie."""
        if rank1 < rank2:
            return -1
        if rank1 > rank2:
            return 1
        return 0

    def hand_strength_pct(self, hole_cards: list[Card], community_cards: list[Card]) -> float:
        """Returns 0.0-1.0 hand strength percentage (1.0 = best possible)."""
        rank = self.evaluate(hole_cards, community_cards)
        # treys rank ranges: best=1 (straight flush), worst=7462 (high card)
        return max(0.0, min(1.0, 1.0 - (rank - 1) / 7461.0))
