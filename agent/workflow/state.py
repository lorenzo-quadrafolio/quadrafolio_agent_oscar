from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


VALID_STATUSES = {
    "pending",
    "ready",
    "waiting_for_decision",
    "waiting_for_applicability",
    "waiting_for_approval",
    "running",
    "completed",
    "not_applicable",
    "failed",
    "blocked",
}


@dataclass
class TaskState:
    task_id: str
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    decision_made: bool = False
    approval_granted: bool = False
    applicable: Optional[bool] = None

    def set_status(self, status: str) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid task status: {status}")

        self.status = status
        now = datetime.now(timezone.utc).isoformat()

        if status == "running" and self.started_at is None:
            self.started_at = now

        if status in {"completed", "not_applicable"}:
            self.completed_at = now


@dataclass
class WorkflowState:
    workflow_id: str
    tasks: Dict[str, TaskState] = field(default_factory=dict)

    def task(self, task_id: str) -> TaskState:
        if task_id not in self.tasks:
            raise KeyError(f"Unknown task_id: {task_id}")
        return self.tasks[task_id]

    def completed_task_ids(self) -> set[str]:
        return {
            task_id
            for task_id, state in self.tasks.items()
            if state.status in {"completed", "not_applicable"}
        }

    def initialize(self, task_ids: list[str]) -> None:
        for task_id in task_ids:
            if task_id not in self.tasks:
                self.tasks[task_id] = TaskState(task_id=task_id)
