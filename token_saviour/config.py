"""
Config — Configuration loader for Claude Token Saviour.

Reads configuration from YAML files and environment variables.
Provides sensible defaults for all settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# Try to import yaml; fall back gracefully
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# Default configuration values
DEFAULT_CONFIG = {
    "models": {
        "simple": "claude-3-5-haiku-20241022",
        "moderate": "claude-sonnet-4-20250514",
        "complex": "claude-opus-4-20250514",
    },
    "routing": {
        "default_tier": "moderate",
        "auto_fallback": True,
        "max_retries": 1,
    },
    "budget": {
        "daily_limit_usd": 10.00,
        "alert_threshold_pct": 80,
    },
    "tracking": {
        "enabled": True,
        "data_file": "usage_data.json",
    },
    "optimization": {
        "compress_prompts": True,
        "strip_comments": False,
        "suggest_max_tokens": True,
    },
}


@dataclass
class Config:
    """
    Configuration manager for Claude Token Saviour.

    Loads settings from (in priority order):
    1. Environment variables (CLAUDE_TS_* prefix)
    2. YAML config file
    3. Default values
    """

    config_path: Optional[str] = None
    _data: dict[str, Any] = field(default_factory=dict, repr=False)
    _loaded: bool = field(default=False, repr=False)

    def __post_init__(self):
        self._load()

    def _load(self) -> None:
        """Load configuration from file and environment."""
        # Start with defaults
        self._data = _deep_copy(DEFAULT_CONFIG)

        # Try to load from YAML file
        config_file = self._find_config_file()
        if config_file and HAS_YAML:
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}
                _deep_merge(self._data, file_config)
            except (yaml.YAMLError, OSError):
                pass  # Fall back to defaults

        # Override with environment variables
        self._apply_env_overrides()
        self._loaded = True

    def _find_config_file(self) -> Optional[str]:
        """Find the config file, checking multiple locations."""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path

        # Search order
        search_paths = [
            "config.yaml",
            "config.yml",
            os.path.expanduser("~/.claude_token_saviour/config.yaml"),
            os.path.expanduser("~/.config/claude_token_saviour/config.yaml"),
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        return None

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides (CLAUDE_TS_* prefix)."""
        env_mappings = {
            "CLAUDE_TS_MODEL_SIMPLE": ("models", "simple"),
            "CLAUDE_TS_MODEL_MODERATE": ("models", "moderate"),
            "CLAUDE_TS_MODEL_COMPLEX": ("models", "complex"),
            "CLAUDE_TS_DEFAULT_TIER": ("routing", "default_tier"),
            "CLAUDE_TS_AUTO_FALLBACK": ("routing", "auto_fallback"),
            "CLAUDE_TS_DAILY_LIMIT": ("budget", "daily_limit_usd"),
            "CLAUDE_TS_DATA_FILE": ("tracking", "data_file"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Type conversion
                if key in ("auto_fallback",):
                    value = value.lower() in ("true", "1", "yes")
                elif key in ("daily_limit_usd", "alert_threshold_pct"):
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                elif key in ("max_retries",):
                    try:
                        value = int(value)
                    except ValueError:
                        continue

                if section not in self._data:
                    self._data[section] = {}
                self._data[section][key] = value

    @property
    def models(self) -> dict[str, str]:
        """Get model configuration."""
        return self._data.get("models", DEFAULT_CONFIG["models"])

    @property
    def routing(self) -> dict[str, Any]:
        """Get routing configuration."""
        return self._data.get("routing", DEFAULT_CONFIG["routing"])

    @property
    def budget(self) -> dict[str, Any]:
        """Get budget configuration."""
        return self._data.get("budget", DEFAULT_CONFIG["budget"])

    @property
    def tracking(self) -> dict[str, Any]:
        """Get tracking configuration."""
        return self._data.get("tracking", DEFAULT_CONFIG["tracking"])

    @property
    def optimization(self) -> dict[str, Any]:
        """Get optimization configuration."""
        return self._data.get("optimization", DEFAULT_CONFIG["optimization"])

    def get(self, key: str, default: Any = None) -> Any:
        """Get a top-level config value."""
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return _deep_copy(self._data)

    def save(self, path: Optional[str] = None) -> None:
        """Save the current configuration to a YAML file."""
        if not HAS_YAML:
            raise ImportError("PyYAML is required to save config. Install with: pip install pyyaml")

        save_path = path or self.config_path or "config.yaml"
        parent = Path(save_path).parent
        if parent != Path("."):
            parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)


def _deep_copy(d: dict) -> dict:
    """Deep copy a nested dictionary."""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _deep_copy(value)
        elif isinstance(value, list):
            result[key] = list(value)
        else:
            result[key] = value
    return result


def _deep_merge(base: dict, override: dict) -> None:
    """Deep merge override into base (mutates base)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
