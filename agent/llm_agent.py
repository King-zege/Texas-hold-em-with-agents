"""LLM-powered agent using Anthropic Claude API."""

import os
import json
import re
from agent.base_agent import BaseAgent
from agent.observation import Observation
from engine.action import Action, ActionType


# Tool definition for poker action (BigModel format)
POKER_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "poker_action",
        "description": "在德州扑克中执行动作",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["fold", "call", "check", "bet", "raise", "all_in"],
                    "description": "要执行的动作类型"
                },
                "amount": {
                    "type": "number",
                    "description": "下注/加注金额（BB为单位），仅bet/raise时需要"
                }
            },
            "required": ["action"]
        }
    }
}


class LLMAgent(BaseAgent):
    """Agent that uses LLM to make poker decisions."""

    def __init__(
        self,
        player_id: str,
        api_key: str | None = None,
        api_base: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "glm-4.6V",
        style: str = "balanced",
    ):
        self.player_id = player_id
        self.style = style
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.api_base = api_base.rstrip("/")
        self.model = model
        self._call_count = 0  # Debug counter

    def decide(self, observation: Observation, legal_actions: list[Action]) -> Action:
        """Use LLM to decide which action to take."""
        self._call_count += 1
        import time
        start_time = time.time()

        prompt = self._build_prompt(observation, legal_actions)

        try:
            response, num_calls = self._call_llm_with_count(prompt)
            elapsed = time.time() - start_time
            print(f"  👨 {self.player_id} 思考{elapsed:.1f}s后行动：", end=" ", flush=True)
            action = self._parse_action(response, legal_actions, observation)
            if action is not None and action in legal_actions:
                return action
        except Exception as e:
            print(f"\n  [LLM Error #{self._call_count}] {e}")

        # Fallback to first legal action
        print(f"  👨 {self.player_id} 思考{time.time()-start_time:.1f}s后行动：", end=" ", flush=True)
        return legal_actions[0]

    def explain(self, observation: Observation, chosen_action: Action) -> str:
        """Generate explanation using LLM."""
        prompt = f"""德州扑克：玩家 {self.player_id} 选择 {chosen_action}。
请简短解释原因（10字以内）。"""
        try:
            return self._call_llm(prompt)
        except:
            return f"LLM: {chosen_action}"

    def _build_prompt(self, obs: Observation, legal_actions: list[Action]) -> str:
        """Build a compact prompt for the LLM."""
        hole_cards = " ".join(str(c) for c in obs.hole_cards)
        community = " ".join(str(c) for c in obs.community_cards) if obs.community_cards else "无"

        # Build compact actions list
        actions_list = []
        for i, a in enumerate(legal_actions):
            if a.amount > 0:
                actions_list.append(f"{i+1}.{a.type.value.upper()}:{a.amount}")
            else:
                actions_list.append(f"{i+1}.{a.type.value.upper()}")
        actions_str = " ".join(actions_list)

        street_map = {"preflop": "翻前", "flop": "翻牌", "turn": "转牌", "river": "河牌"}
        street = street_map.get(obs.street, obs.street)

        return f"""扑克：你{self.player_id}在{obs.position_name}({street})
手牌{hole_cards} 公共{community} 池{obs.pot_bb:.1f}BB 跟注{obs.current_bet_to_call_bb:.1f}BB 筹码{obs.stack_bb:.1f}BB
可选动作: {actions_str}
直接返回: {{"a":"1"}} 或 {{"a":"fold"}}"""

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API with tool support."""
        import urllib.request
        import urllib.error

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 512,
            "tools": [POKER_ACTION_TOOL],
        }

        url = f"{self.api_base}/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return self._extract_content(result)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"LLM Call Failed: {e}")

    def _call_llm_with_count(self, prompt: str) -> tuple[str, int]:
        """Call LLM API and return content plus call count."""
        import urllib.request
        import urllib.error

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        messages = [{"role": "user", "content": prompt}]
        call_count = 0

        url = f"{self.api_base}/chat/completions"

        while True:
            call_count += 1

            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 512,
                "tools": [POKER_ACTION_TOOL],
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8") if e.fp else ""
                raise Exception(f"HTTP {e.code}: {error_body}")
            except Exception as e:
                raise Exception(f"LLM Call Failed: {e}")

            choices = result.get("choices", [])
            if not choices:
                raise Exception("No choices in response")

            msg = choices[0].get("message", {})

            # Check for tool_call
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                # Extract assistant's reasoning (any text content before tool call)
                content = msg.get("content", "") or ""
                # Add assistant message with tool_call to messages
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls
                })
                # Process each tool_call and add tool response
                for call in tool_calls:
                    if call.get("function", {}).get("name") == "poker_action":
                        # This is our poker action tool - extract and return immediately
                        args = call.get("function", {}).get("arguments", "{}")
                        try:
                            args_dict = json.loads(args) if isinstance(args, str) else args
                            action = args_dict.get("action", "")
                            amount = args_dict.get("amount")
                            return json.dumps({"a": action, "amt": amount}), call_count
                        except:
                            pass
                    # Add generic tool response for other tools
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": "{}"
                    })
                continue

            # No tool call, return content
            content = msg.get("content", "")
            if content:
                return content.strip(), call_count

            # Fallback to reasoning_content
            reasoning = msg.get("reasoning_content", "")
            if reasoning:
                return reasoning.strip(), call_count

            raise Exception("No content or tool_call found")

    def _extract_content(self, result: dict) -> str:
        """Extract text or tool_use content from API response."""
        choices = result.get("choices", [])
        if not choices:
            return ""

        msg = choices[0].get("message", {})

        # Check for tool_call first
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            # Extract action from tool call
            for call in tool_calls:
                if call.get("function", {}).get("name") == "poker_action":
                    args = call.get("function", {}).get("arguments", "{}")
                    try:
                        args_dict = json.loads(args) if isinstance(args, str) else args
                        action = args_dict.get("action", "")
                        amount = args_dict.get("amount")
                        return json.dumps({"a": action, "amt": amount})
                    except:
                        pass

        # Fallback to content
        content = msg.get("content", "")
        if content:
            return content.strip()

        # Fallback: check reasoning_content
        reasoning = msg.get("reasoning_content", "")
        if reasoning:
            return reasoning.strip()

        return ""

    def _parse_chinese_action(self, text: str) -> Action | None:
        """Try to parse a Chinese text response for action keywords."""
        keywords = {
            "弃牌": ActionType.FOLD,
            "fold": ActionType.FOLD,
            "f": ActionType.FOLD,
            "跟注": ActionType.CALL,
            "call": ActionType.CALL,
            "c": ActionType.CALL,
            "过牌": ActionType.CHECK,
            "check": ActionType.CHECK,
            "x": ActionType.CHECK,
            "加注": ActionType.RAISE,
            "raise": ActionType.RAISE,
            "r": ActionType.RAISE,
            "bet": ActionType.BET,
            "b": ActionType.BET,
            "全押": ActionType.ALL_IN,
            "all_in": ActionType.ALL_IN,
            "allin": ActionType.ALL_IN,
            "a": ActionType.ALL_IN,
        }

        text_lower = text.lower()
        for keyword, action_type in keywords.items():
            if keyword in text_lower:
                return action_type

        return None

    def _parse_action(
        self, response: str, legal_actions: list[Action], obs: Observation
    ) -> Action | None:
        """Parse LLM response to get action."""
        try:
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()

            # Find JSON object
            match = re.search(r"\{[^}]+\}", response, re.DOTALL)
            if not match:
                match = re.search(r'"(?:a|action)"\s*:\s*"?([^",}]+)"?', response, re.IGNORECASE)

            if not match:
                chinese_action = self._parse_chinese_action(response)
                if chinese_action:
                    for action in legal_actions:
                        if action.type == chinese_action:
                            return self._make_action(action, None, obs)
                    return self._make_action(legal_actions[0], None, obs)
                return None

            if "{" in match.group(0):
                json_str = match.group(0)
            else:
                action_val = match.group(1).strip()
                for i, action in enumerate(legal_actions):
                    if action.type.value == action_val.lower() or str(i+1) == action_val:
                        return self._make_action(action, None, obs)
                return None

            data = json.loads(json_str)
            action_str = str(data.get("a", data.get("action", ""))).strip()
            amount = data.get("amt", data.get("amount"))

            if action_str.isdigit():
                idx = int(action_str) - 1
                if 0 <= idx < len(legal_actions):
                    return self._make_action(legal_actions[idx], amount, obs)

            action_lower = action_str.lower()
            for action in legal_actions:
                if action.type.value == action_lower or action_lower in action.type.value:
                    return self._make_action(action, amount, obs)

            for action in legal_actions:
                if action.type.value.startswith(action_lower):
                    return self._make_action(action, amount, obs)

            return None

        except Exception as e:
            print(f"[LLM Parse Error] {e}")
            return None

    def _make_action(self, action: Action, amount, obs: Observation) -> Action:
        """Create action with proper amount."""
        if action.type == ActionType.ALL_IN:
            return Action(ActionType.ALL_IN, obs.stack_bb)
        elif action.type in (ActionType.BET, ActionType.RAISE) and amount:
            return Action(action.type, float(amount))
        return action
