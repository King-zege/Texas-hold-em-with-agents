"""Phase 1 agent: selects a weighted random legal action."""

import random
from agent.base_agent import BaseAgent
from agent.observation import Observation
from engine.action import Action, ActionType


class RuleAgent(BaseAgent):
    """Phase 1 agent: selects a weighted random legal action.

    Not truly 'intelligent' but ensures the game loop works end-to-end.
    Weighted slightly toward call/check to avoid everyone folding.
    """

    def __init__(self, player_id: str, style: str = "rule"):
        self.player_id = player_id
        self.style = style

    def decide(self, observation: Observation, legal_actions: list[Action]) -> Action:
        # Weight: fold=1, check=5, call=4, bet/raise=2, all_in=0.5
        weights: list[float] = []
        for a in legal_actions:
            if a.type == ActionType.FOLD:
                weights.append(1.0)
            elif a.type == ActionType.CHECK:
                weights.append(5.0)
            elif a.type == ActionType.CALL:
                weights.append(4.0)
            elif a.type in (ActionType.BET, ActionType.RAISE):
                weights.append(2.0)
            elif a.type == ActionType.ALL_IN:
                weights.append(0.5)
            else:
                weights.append(1.0)

        return random.choices(legal_actions, weights=weights, k=1)[0]

    def explain(self, observation: Observation, chosen_action: Action) -> str:
        return f"Random rule-based decision: {chosen_action}"
