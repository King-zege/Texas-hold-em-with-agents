"""Style-weighted poker agent using style profiles and hand strength."""

import random
from agent.base_agent import BaseAgent
from agent.observation import Observation
from engine.action import Action, ActionType
from strategy.style_profile import StyleProfile
from strategy.preflop_table import preflop_hand_strength
from strategy.postflop_heuristic import postflop_hand_strength


class StyleAgent(BaseAgent):
    """Phase 2 agent: uses style profile to weight actions."""

    def __init__(self, player_id: str, style_profile: StyleProfile):
        self.player_id = player_id
        self.style = style_profile

    def decide(self, observation: Observation, legal_actions: list[Action]) -> Action:
        """Three-step decision: evaluate strength → get weights → pick weighted random."""
        hand_strength = self._evaluate_hand_strength(observation)
        weights = self._compute_action_weights(observation, legal_actions, hand_strength)

        # Weighted random selection
        return random.choices(legal_actions, weights=weights, k=1)[0]

    def explain(self, observation: Observation, chosen_action: Action) -> str:
        """Generate explanation based on style and hand strength."""
        hand_strength = self._evaluate_hand_strength(observation)
        strength_desc = self._strength_description(hand_strength)
        style_name = self.style.display_name

        # Basic explanation based on action type
        if chosen_action.type == ActionType.FOLD:
            if hand_strength < 0.3:
                return f"{style_name} - 弃牌弱手牌 ({strength_desc})"
            else:
                return f"{style_name} - 放弃位置 ({strength_desc})"
        elif chosen_action.type in (ActionType.BET, ActionType.RAISE):
            if hand_strength > 0.7:
                return f"{style_name} - 用强牌加注 ({strength_desc})"
            else:
                return f"{style_name} - 诈唬/施压 ({strength_desc})"
        elif chosen_action.type == ActionType.CALL:
            return f"{style_name} - 跟注看牌 ({strength_desc})"
        elif chosen_action.type == ActionType.CHECK:
            return f"{style_name} - 过牌 ({strength_desc})"
        elif chosen_action.type == ActionType.ALL_IN:
            return f"{style_name} - 全押 ({strength_desc})"
        return f"{style_name} - 随机风格决策"

    def _evaluate_hand_strength(self, obs: Observation) -> float:
        """Returns 0.0-1.0 hand strength score."""
        if obs.street == "preflop":
            return preflop_hand_strength(
                obs.hole_cards,
                obs.position_name,
                obs.num_players,
            )
        else:
            return postflop_hand_strength(
                obs.hole_cards,
                obs.community_cards,
            )

    def _strength_description(self, strength: float) -> str:
        """Return Chinese description of strength category."""
        if strength >= 0.8:
            return "强牌"
        elif strength >= 0.6:
            return "好牌"
        elif strength >= 0.4:
            return "中等牌"
        elif strength >= 0.2:
            return "弱牌"
        else:
            return "垃圾牌"

    def _compute_action_weights(
        self,
        obs: Observation,
        legal_actions: list[Action],
        hand_strength: float,
    ) -> list[float]:
        """Use style profile to weight each legal action."""
        tendency = self.style.get_street_tendency(obs.street)

        # Base weights from style
        weight_map = {
            ActionType.FOLD: tendency.fold_weight,
            ActionType.CHECK: tendency.check_weight,
            ActionType.CALL: tendency.call_weight,
            ActionType.BET: tendency.bet_weight,
            ActionType.RAISE: tendency.raise_weight,
            ActionType.ALL_IN: tendency.all_in_weight,
        }

        # Get base weights for legal actions
        weights = [weight_map[a.type] for a in legal_actions]

        # Adjust based on hand strength vs thresholds
        for i, action in enumerate(legal_actions):
            action_type = action.type
            adjusted_weight = weights[i]

            # Fold more with weak hands, less with strong hands
            if action_type == ActionType.FOLD:
                if hand_strength < self.style.open_threshold * 0.5:
                    adjusted_weight *= 2.0  # Fold weak hands more
                elif hand_strength > self.style.call_threshold:
                    adjusted_weight *= 0.3  # Don't fold strong hands

            # Check/back with medium hands in position
            elif action_type == ActionType.CHECK:
                if obs.position_name in ("CO", "BTN", "SB"):
                    adjusted_weight *= 1.5
                else:
                    adjusted_weight *= 0.8

            # Call appropriate hands
            elif action_type == ActionType.CALL:
                call_amount = obs.current_bet_to_call_bb
                pot_odds = obs.pot_bb / (call_amount + obs.pot_bb) if call_amount > 0 else 0
                if pot_odds > 0.5:  # Good pot odds
                    adjusted_weight *= 1.5
                if hand_strength > self.style.reraise_threshold:
                    adjusted_weight *= 0.5  # Might want to raise instead

            # Bet/raise with strong hands
            elif action_type in (ActionType.BET, ActionType.RAISE):
                if hand_strength > self.style.reraise_threshold:
                    adjusted_weight *= 2.0  # Value bet with strong hands
                elif hand_strength < self.style.open_threshold:
                    # Bluff
                    if random.random() < tendency.bluff_frequency:
                        adjusted_weight *= 1.5  # Bluff as intended
                    else:
                        adjusted_weight *= 0.2  # Don't bluff with weak hands
                else:
                    # Medium strength - moderate betting
                    adjusted_weight *= 1.2

            # All-in with premium hands
            elif action_type == ActionType.ALL_IN:
                if hand_strength > 0.8 and obs.spr < 5:
                    adjusted_weight *= 2.0
                elif hand_strength < 0.3:
                    adjusted_weight *= 0.1
                else:
                    adjusted_weight *= 0.5

            weights[i] = adjusted_weight

        # Normalize weights
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        else:
            weights = [1.0 / len(legal_actions)] * len(legal_actions)

        return weights
