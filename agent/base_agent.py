"""Abstract base class for all poker agents."""

from abc import ABC, abstractmethod
from agent.observation import Observation
from engine.action import Action


class BaseAgent(ABC):
    """Abstract base class for all poker agents.

    Every agent must implement decide() and explain().
    """

    @abstractmethod
    def decide(self, observation: Observation, legal_actions: list[Action]) -> Action:
        """Given an observation and list of legal actions, return one action.

        Must return exactly one action from legal_actions.
        """
        ...

    @abstractmethod
    def explain(self, observation: Observation, chosen_action: Action) -> str:
        """Return a human-readable explanation of why this action was chosen.

        Used for decision log and hand history analysis.
        """
        ...
