"""Model versioning and registry."""
import json
import os
from datetime import datetime
from pathlib import Path


class ModelRegistry:
    """Track model versions and metadata locally."""

    def __init__(self, registry_dir: str = "data/models"):
        self.registry_dir = Path(registry_dir)
        self.registry_file = self.registry_dir / "registry.json"
        self._registry = self._load()

    def _load(self) -> dict:
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"models": {}, "active": None}

    def _save(self):
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self._registry, f, indent=2, default=str)

    def register(self, name: str, version: str, metrics: dict, path: str):
        """Register a new model version."""
        if name not in self._registry["models"]:
            self._registry["models"][name] = []

        self._registry["models"][name].append({
            "version": version,
            "metrics": metrics,
            "path": path,
            "registered_at": datetime.utcnow().isoformat(),
        })
        self._save()

    def set_active(self, name: str, version: str):
        """Set the active model for inference."""
        self._registry["active"] = {"name": name, "version": version}
        self._save()

    def get_active(self) -> dict:
        """Get the currently active model info."""
        return self._registry.get("active")

    def list_versions(self, name: str) -> list:
        """List all versions of a model."""
        return self._registry.get("models", {}).get(name, [])
