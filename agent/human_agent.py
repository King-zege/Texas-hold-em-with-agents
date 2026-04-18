"""Human player agent: prompts user for decisions."""

import sys
from agent.base_agent import BaseAgent
from agent.observation import Observation
from engine.action import Action, ActionType


class HumanAgent(BaseAgent):
    """Agent that prompts the human player for decisions."""

    def __init__(self, player_id: str, style: str = "human"):
        self.player_id = player_id
        self.style = style

    def _get_line(self, prompt: str) -> str:
        """Get input line - works with both console and redirected stdin."""
        print(prompt, end='', flush=True)
        sys.stdout.flush()

        try:
            # Use stdin.buffer for binary mode, then decode
            # This avoids Windows text-mode buffering issues with pipes
            if hasattr(sys.stdin, 'buffer'):
                line_bytes = sys.stdin.buffer.readline()
                if not line_bytes:
                    raise EOFError()
                return line_bytes.decode('utf-8', errors='replace').rstrip('\r\n')
            else:
                line = sys.stdin.readline()
                if not line:
                    raise EOFError()
                return line.rstrip('\r\n')
        except EOFError:
            raise
        except Exception as e:
            print(f"Input error: {e}")
            raise EOFError()

    def decide(self, observation: Observation, legal_actions: list[Action]) -> Action:
        """Prompt human for their decision."""
        self._print_observation(observation, legal_actions)

        while True:
            try:
                choice = self._get_line(f"\n> {self.player_id} 请选择动作 (输入编号或动作名): ").strip()

                if not choice:
                    print("请输入有效的选择")
                    continue

                # Try to parse as number
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(legal_actions):
                        action = legal_actions[idx]
                        if action.type == ActionType.ALL_IN:
                            # ALL_IN uses all remaining stack automatically
                            return Action(action.type, observation.stack_bb)
                        elif action.type in (ActionType.BET, ActionType.RAISE):
                            amount = self._get_amount(action, observation)
                            if amount is None:
                                # Cancelled - re-prompt for action
                                self._print_observation(observation, legal_actions)
                                continue
                            return Action(action.type, amount)
                        return action
                    else:
                        print(f"编号 {choice} 无效，有效范围: 1-{len(legal_actions)}")
                        continue

                # Try to parse as action name
                action_lower = choice.lower()
                for action in legal_actions:
                    if action.type.value == action_lower:
                        if action.type == ActionType.ALL_IN:
                            # ALL_IN uses all remaining stack automatically
                            return Action(action.type, observation.stack_bb)
                        elif action.type in (ActionType.BET, ActionType.RAISE):
                            amount = self._get_amount(action, observation)
                            if amount is None:
                                # Cancelled - re-prompt for action
                                self._print_observation(observation, legal_actions)
                                continue
                            return Action(action.type, amount)
                        return action

                # Handle amount-only input
                try:
                    amount = float(choice)
                    for action in legal_actions:
                        if action.type in (ActionType.BET, ActionType.RAISE):
                            if amount >= action.amount:
                                return Action(action.type, amount)
                    print(f"金额 {amount} 对于可选的下注/加注无效")
                except ValueError:
                    pass

                print(f"无效选择，有效选项: {', '.join(a.type.value for a in legal_actions)}")
            except EOFError:
                return legal_actions[0]
            except Exception as e:
                print(f"错误: {e}")

    def _print_observation(self, obs: Observation, legal_actions: list[Action]) -> None:
        """Print game state for human player."""
        print(f"\n{'='*50}")
        print(f"【{self.player_id}】你的回合")
        print(f"{'='*50}")

        print(f"位置: {obs.position_name}")

        cards = " ".join(str(c) for c in obs.hole_cards)
        print(f"手牌: {cards}")

        if obs.community_cards:
            cc = " ".join(str(c) for c in obs.community_cards)
            street_display = {"flop": "翻牌", "turn": "转牌", "river": "河牌"}.get(obs.street, obs.street)
            print(f"公共牌 ({street_display}): {cc}")

        print(f"\n底池: {obs.pot_bb:.1f}BB")

        to_call = obs.current_bet_to_call_bb
        if to_call > 0:
            print(f"需要跟注: {to_call:.1f}BB")
        else:
            print("无人下注，你可以选择过牌或下注")

        print(f"你的筹码: {obs.stack_bb:.1f}BB")
        print(f"SPR: {obs.spr:.1f}")

        if obs.actions_this_street:
            print("\n本街已有动作:")
            for pid, action, pos_name, stack in obs.actions_this_street:
                pos_display = f"({pos_name})" if pos_name else ""
                stack_display = f"[{stack:.1f}BB]" if stack else ""
                print(f"  {pid} {pos_display} {stack_display}: {action}")

        print("\n可选动作:")
        for i, action in enumerate(legal_actions, 1):
            desc = self._describe_action(action, to_call, obs)
            print(f"  {i}. {action.type.value} {desc}")

    def _describe_action(self, action: Action, to_call: float, obs: Observation) -> str:
        """Get description of an action."""
        if action.type == ActionType.FOLD:
            return "(弃牌)"
        elif action.type == ActionType.CHECK:
            return "(过牌)"
        elif action.type == ActionType.CALL:
            return f"(跟注 {to_call:.1f}BB)"
        elif action.type == ActionType.BET:
            return f"(下注，任意金额 ≥ {action.amount:.1f}BB)"
        elif action.type == ActionType.RAISE:
            return f"(加注，任意金额 ≥ {action.amount:.1f}BB)"
        elif action.type == ActionType.ALL_IN:
            return f"(全押 {obs.stack_bb:.1f}BB - 自动)"
        return ""

    def _get_amount(self, action: Action, obs: Observation) -> float | None:
        """Get bet/raise amount from human. Returns None if cancelled."""
        min_amount = action.amount
        max_amount = obs.max_raise_bb

        print(f"\n下注金额 (最小: {min_amount:.1f}BB, 最大: {max_amount:.1f}BB):")
        print("> 可以输入任意金额，只要在最小和最大之间")
        print("> 例如: 12.0 或 66.6 (直接输入数字即可)")
        print("> 输入 q 或 cancel 可以取消并重新选择动作")

        while True:
            try:
                raw = self._get_line("> 请输入金额: ")
                choice = raw.replace("BB", "").replace("bb", "").strip().lower()

                # Check for cancellation
                if choice in ("q", "quit", "cancel", "c", "取消"):
                    return None

                if not choice:
                    print("请输入有效数字")
                    continue

                amount = float(choice)

                if amount < min_amount:
                    print(f"金额不能小于最小下注额 {min_amount:.1f}BB")
                elif amount > max_amount:
                    print(f"金额不能超过你的最大筹码 {max_amount:.1f}BB")
                else:
                    return amount
            except ValueError:
                print("请输入有效数字")
            except EOFError:
                return min_amount

    def explain(self, observation: Observation, chosen_action: Action) -> str:
        """Human decisions are manually explained."""
        return f"Human player: {chosen_action}"
