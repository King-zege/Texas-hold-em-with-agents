"""Layer 1: Legal action filter. Computes the set of legal actions for a seat."""

from engine.action import Action, ActionType


def compute_legal_actions(
    stack_bb: float,
    current_bet_bb: float,      # This seat's current bet on this street
    highest_bet_bb: float,      # Highest bet on this street
    min_raise_bb: float,        # Minimum legal raise total
    pot_bb: float,
    big_blind_bb: float,
) -> list[Action]:
    """
    Returns list of legal Action objects based on game rules.

    Rules:
    1. If no bet to call (current_bet_bb == highest_bet_bb):
       - CHECK is always legal
       - BET is legal, min = big_blind_bb, max = stack + current_bet
       - ALL_IN is legal
    2. If there is a bet to call (highest_bet_bb > current_bet_bb):
       - FOLD is always legal
       - CALL is legal (match highest_bet_bb, capped at stack)
       - RAISE is legal if stack allows (min_raise_bb to stack + current_bet)
       - ALL_IN is legal
    3. If stack cannot cover the call amount:
       - FOLD is legal
       - ALL_IN (for less than call) is legal
    4. Stack of 0: no actions (shouldn't be asked)
    """
    if stack_bb <= 0:
        return []

    legal: list[Action] = []
    to_call = highest_bet_bb - current_bet_bb

    if to_call <= 0:
        # No bet to call — can check or bet
        legal.append(Action(ActionType.CHECK))

        # BET: first voluntary wager on this street
        min_bet = max(big_blind_bb, highest_bet_bb + big_blind_bb)
        if stack_bb > 0:
            # Can bet at least the minimum if stack allows, or all-in for less
            if stack_bb + current_bet_bb >= min_bet:
                legal.append(Action(ActionType.BET, amount=min_bet))
            # Can always go all-in
            if stack_bb > 0:
                legal.append(Action(ActionType.ALL_IN, amount=stack_bb + current_bet_bb))
    else:
        # There is a bet to call
        legal.append(Action(ActionType.FOLD))

        if stack_bb >= to_call:
            # Can cover the call
            legal.append(Action(ActionType.CALL))

            # Can raise if stack allows going beyond the call
            remaining_after_call = stack_bb - to_call
            if remaining_after_call > 0 and stack_bb + current_bet_bb >= min_raise_bb:
                legal.append(Action(ActionType.RAISE, amount=min_raise_bb))

            # All-in
            legal.append(Action(ActionType.ALL_IN, amount=stack_bb + current_bet_bb))
        else:
            # Cannot cover the call — can go all-in for less
            legal.append(Action(ActionType.ALL_IN, amount=stack_bb + current_bet_bb))

    return legal
