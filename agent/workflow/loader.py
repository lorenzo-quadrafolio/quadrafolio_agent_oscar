from pathlib import Path
from typing import Dict, Any
import yaml


WORKFLOW_DIR = Path("workflows/spv_factory")


class WorkflowLoader:
    """Load and validate machine-readable workflow definitions."""

    def __init__(self, workflow_dir: Path = WORKFLOW_DIR):
        self.workflow_dir = workflow_dir

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """Load every workflow YAML file indexed by task_id."""
        workflows = {}

        for path in sorted(self.workflow_dir.glob("*.yaml")):
            data = self._load_file(path)
            task_id = data["task_id"]

            if task_id in workflows:
                raise ValueError(f"Duplicate task_id: {task_id}")

            workflows[task_id] = data

        if not workflows:
            raise ValueError(
                f"No workflow definitions found in {self.workflow_dir}"
            )

        return workflows

    def load(self, task_id: str) -> Dict[str, Any]:
        """Load one workflow definition by task_id."""
        workflows = self.load_all()

        if task_id not in workflows:
            raise KeyError(f"Unknown task_id: {task_id}")

        return workflows[task_id]

    @staticmethod
    def _load_file(path: Path) -> Dict[str, Any]:
        """Load one YAML file."""
        try:
            data = yaml.safe_load(path.read_text())
        except Exception as exc:
            raise ValueError(
                f"Failed to load {path}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"{path}: workflow definition must be an object"
            )

        return data
