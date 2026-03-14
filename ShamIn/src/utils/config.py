"""ShamIn configuration loader."""
import os
import re
import yaml
from pathlib import Path


_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _resolve_env_vars(value):
    """Replace ${VAR} patterns with environment variable values."""
    if isinstance(value, str):
        pattern = re.compile(r'\$\{([^}]+)\}')
        def replacer(match):
            return os.getenv(match.group(1), '')
        return pattern.sub(replacer, value)
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def load_config(filename: str) -> dict:
    """Load a YAML config file from config/ directory, resolving env vars."""
    filepath = _CONFIG_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    return _resolve_env_vars(raw)


def get_settings() -> dict:
    return load_config("settings.yaml")


def get_sources() -> dict:
    return load_config("sources.yaml")


def get_model_config() -> dict:
    return load_config("model_config.yaml")


def get_alerts_config() -> dict:
    return load_config("alerts.yaml")
