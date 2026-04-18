"""Pot management including side pot calculation."""

from dataclasses import dataclass, field
from engine.card import Card
from engine.hand_evaluator import HandEvaluator


@dataclass
class Pot:
    """A single pot (main or side) with eligible seat indices."""
    amount_bb: float
    eligible_seats: list[int]  # Indices of seats eligible to win this pot


@dataclass
class PotWinner:
    """Winner of a pot or share of a split pot."""
    seat_index: int
    amount_bb: float
    hand_name: str


class PotManager:
    """Calculates main pot and side pots, then awards them at showdown."""

    @staticmethod
    def calculate_pots(
        total_bets: list[float],  # total_bet_bb per seat
        folded: list[bool],       # folded status per seat
    ) -> list[Pot]:
        """
        Water-filling side pot algorithm.

        Each seat's total_bet_bb may differ. All-in players create side pots.
        Folded players contribute dead money but are not eligible to win.

        Returns list of Pot objects (main pot first, then side pots).
        """
        n = len(total_bets)
        # Get unique bet levels from non-folded players with bets > 0
        non_folded_bets = [total_bets[i] for i in range(n) if not folded[i] and total_bets[i] > 0]
        if not non_folded_bets:
            # All bets are from folded players only — single pot
            total = sum(total_bets)
            if total > 0:
                # No eligible players — edge case, pot goes to last folder or house
                return []
            return []

        levels = sorted(set(non_folded_bets))
        pots: list[Pot] = []
        prev_level = 0.0

        for level in levels:
            pot_amount = 0.0
            eligible: list[int] = []

            for i in range(n):
                contribution = min(total_bets[i], level) - min(total_bets[i], prev_level)
                pot_amount += contribution
                # Non-folded seats with total bet >= level are eligible
                if not folded[i] and total_bets[i] >= level:
                    eligible.append(i)

            if pot_amount > 0 and eligible:
                pots.append(Pot(amount_bb=round(pot_amount, 2), eligible_seats=eligible))

            prev_level = level

        return pots

    @staticmethod
    def award_pots(
        pots: list[Pot],
        hole_cards: list[list[Card]],  # hole cards per seat
        community_cards: list[Card],
        folded: list[bool],
    ) -> list[PotWinner]:
        """
        Evaluate hands of eligible players for each pot, determine winners.
        Returns list of PotWinner with seat_index, amount, and hand_name.
        """
        evaluator = HandEvaluator()
        winners: list[PotWinner] = []

        for pot in pots:
            # Evaluate hands of eligible seats that haven't folded
            eligible_hands: list[tuple[int, int]] = []  # (seat_index, treys_rank)
            for idx in pot.eligible_seats:
                if not folded[idx] and hole_cards[idx]:
                    rank = evaluator.evaluate(hole_cards[idx], community_cards)
                    eligible_hands.append((idx, rank))

            if not eligible_hands:
                continue

            # Find best rank (lower is better in treys)
            best_rank = min(rank for _, rank in eligible_hands)
            # All players with the best rank split the pot
            winners_idx = [idx for idx, rank in eligible_hands if rank == best_rank]
            share = round(pot.amount_bb / len(winners_idx), 2)
            hand_name = evaluator.rank_name(best_rank)

            for idx in winners_idx:
                winners.append(PotWinner(
                    seat_index=idx,
                    amount_bb=share,
                    hand_name=hand_name,
                ))

        return winners
