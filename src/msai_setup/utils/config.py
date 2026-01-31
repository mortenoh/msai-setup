"""Configuration file handling."""

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "msai" / "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        path: Path to config file. Uses default if None.

    Returns:
        Configuration dictionary, empty if file doesn't exist.
    """
    config_path = path or DEFAULT_CONFIG_PATH

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict[str, Any], path: Path | None = None) -> None:
    """Save configuration to YAML file.

    Args:
        config: Configuration dictionary to save.
        path: Path to config file. Uses default if None.
    """
    config_path = path or DEFAULT_CONFIG_PATH

    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def get_config_value(
    key: str,
    default: Any = None,
    path: Path | None = None,
) -> Any:
    """Get a configuration value by key.

    Supports dot notation for nested keys (e.g., 'zfs.pool_name').

    Args:
        key: Configuration key, supports dot notation.
        default: Default value if key not found.
        path: Path to config file. Uses default if None.

    Returns:
        Configuration value or default.
    """
    config: dict[str, Any] = load_config(path)
    keys = key.split(".")

    current: dict[str, Any] = config
    for i, k in enumerate(keys):
        if k not in current:
            return default
        value = current[k]
        if i == len(keys) - 1:
            return value
        if not isinstance(value, dict):
            return default
        current = value  # pyright: ignore[reportUnknownVariableType]

    return default
