"""Load and validate LifePathConfig from YAML/JSON files at startup."""

import json
from pathlib import Path

import yaml

from models.content import LifePathConfig

# In-memory registry populated at startup
_configs: dict[str, LifePathConfig] = {}

STAGES_DIR = Path(__file__).parent / "stages"


def load_all_configs() -> dict[str, LifePathConfig]:
    """Deserialize all YAML/JSON files in content/stages/ into LifePathConfig objects.

    Validates cross-references via LifePathConfig.model_validator on load.
    Raises on any invalid config so the server fails fast at startup.
    """
    global _configs
    _configs = {}

    for path in sorted(STAGES_DIR.iterdir()):
        if path.suffix in {".yaml", ".yml"}:
            raw = yaml.safe_load(path.read_text())
        elif path.suffix == ".json":
            raw = json.loads(path.read_text())
        else:
            continue

        config = LifePathConfig.model_validate(raw)
        if config.id in _configs:
            raise ValueError(
                f"Duplicate LifePathConfig id '{config.id}' found in '{path.name}'"
            )
        _configs[config.id] = config

    return _configs


def get_config(config_id: str) -> LifePathConfig:
    """Return a loaded LifePathConfig by id, or raise KeyError."""
    if config_id not in _configs:
        raise KeyError(f"LifePathConfig '{config_id}' not found")
    return _configs[config_id]


def all_configs() -> dict[str, LifePathConfig]:
    return dict(_configs)
