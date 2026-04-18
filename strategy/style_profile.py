"""Style profile dataclasses and loader."""

import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class StreetTendency:
    """Action tendency weights for one street."""
    fold_weight: float = 1.0
    check_weight: float = 1.0
    call_weight: float = 1.0
    bet_weight: float = 1.0
    raise_weight: float = 1.0
    all_in_weight: float = 0.5
    # Bet sizing as % of pot
    small_bet_pct: float = 0.33
    medium_bet_pct: float = 0.50
    large_bet_pct: float = 0.75
    # Tendencies
    bluff_frequency: float = 0.0  # 0-1
    cbet_frequency: float = 0.0


@dataclass
class StyleProfile:
    """Complete style definition with thresholds and per-street tendencies."""
    name: str
    display_name: str
    description: str

    # Preflop range width
    preflop_vpip: float  # Voluntarily Put $ In Pot %
    preflop_pfr: float   # Preflop Raise %

    # Hand strength thresholds (0-1)
    open_threshold: float
    call_threshold: float
    reraise_threshold: float
    defend_bb_threshold: float

    # Per-street tendencies
    preflop: StreetTendency
    flop: StreetTendency
    turn: StreetTendency
    river: StreetTendency

    @classmethod
    def from_yaml(cls, path: str) -> "StyleProfile":
        """Load style profile from YAML config file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Load each street's tendency
        streets = {}
        for street_name in ["preflop", "flop", "turn", "river"]:
            street_data = data.get(street_name, {})
            streets[street_name] = StreetTendency(
                fold_weight=street_data.get("fold_weight", 1.0),
                check_weight=street_data.get("check_weight", 1.0),
                call_weight=street_data.get("call_weight", 1.0),
                bet_weight=street_data.get("bet_weight", 1.0),
                raise_weight=street_data.get("raise_weight", 1.0),
                all_in_weight=street_data.get("all_in_weight", 0.5),
                small_bet_pct=street_data.get("small_bet_pct", 0.33),
                medium_bet_pct=street_data.get("medium_bet_pct", 0.50),
                large_bet_pct=street_data.get("large_bet_pct", 0.75),
                bluff_frequency=street_data.get("bluff_frequency", 0.0),
                cbet_frequency=street_data.get("cbet_frequency", 0.0),
            )

        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            preflop_vpip=data["preflop_vpip"],
            preflop_pfr=data["preflop_pfr"],
            open_threshold=data["open_threshold"],
            call_threshold=data["call_threshold"],
            reraise_threshold=data["reraise_threshold"],
            defend_bb_threshold=data["defend_bb_threshold"],
            preflop=streets["preflop"],
            flop=streets["flop"],
            turn=streets["turn"],
            river=streets["river"],
        )

    def get_street_tendency(self, street: str) -> StreetTendency:
        """Get StreetTendency for the given street name."""
        street_map = {
            "preflop": self.preflop,
            "flop": self.flop,
            "turn": self.turn,
            "river": self.river,
        }
        return street_map.get(street, self.flop)


class StyleRegistry:
    """Registry of all available style profiles."""

    def __init__(self, styles_dir: str = "config/styles"):
        self._styles_dir = Path(styles_dir)
        self._styles: dict[str, StyleProfile] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all style YAML files from styles directory."""
        if not self._styles_dir.exists():
            raise FileNotFoundError(f"Styles directory not found: {self._styles_dir}")

        for yaml_file in self._styles_dir.glob("*.yaml"):
            profile = StyleProfile.from_yaml(str(yaml_file))
            self._styles[profile.name.lower()] = profile

    def get(self, style_name: str) -> StyleProfile | None:
        """Get a style profile by name (case-insensitive)."""
        return self._styles.get(style_name.lower())

    def list_styles(self) -> list[str]:
        """Return list of available style names."""
        return list(self._styles.keys())
