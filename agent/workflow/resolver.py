from typing import Dict, Any, List, Set


class WorkflowResolver:
    """Resolve workflow task readiness from task dependencies."""

    def __init__(self, workflows: Dict[str, Dict[str, Any]]):
        self.workflows = workflows

    def is_complete(
        self,
        task_id: str,
        completed: Set[str],
    ) -> bool:
        return task_id in completed

    def blockers(
        self,
        task_id: str,
        completed: Set[str],
    ) -> List[str]:
        """Return incomplete dependencies for a task."""
        task = self.workflows[task_id]

        return [
            dependency
            for dependency in task["dependencies"]
            if dependency not in completed
        ]

    def is_ready(
        self,
        task_id: str,
        completed: Set[str],
    ) -> bool:
        """A task is ready when all dependencies are complete."""
        return (
            task_id not in completed
            and not self.blockers(task_id, completed)
        )

    def ready_tasks(
        self,
        completed: Set[str],
    ) -> List[str]:
        """Return all currently ready tasks in deterministic order."""
        return sorted(
            task_id
            for task_id in self.workflows
            if self.is_ready(task_id, completed)
        )

    def blocked_tasks(
        self,
        completed: Set[str],
    ) -> Dict[str, List[str]]:
        """Return blocked tasks and their incomplete dependencies."""
        return {
            task_id: self.blockers(task_id, completed)
            for task_id in sorted(self.workflows)
            if (
                task_id not in completed
                and self.blockers(task_id, completed)
            )
        }

    def next_tasks(
        self,
        completed: Set[str],
    ) -> List[Dict[str, Any]]:
        """
        Return all currently actionable tasks with execution metadata.

        No task is selected over another when multiple tasks are ready.
        """
        return [
            {
                "task_id": task_id,
                "name": self.workflows[task_id]["name"],
                "phase": self.workflows[task_id]["phase"],
                "decision": self.workflows[task_id]["decision"],
                "execution": self.workflows[task_id]["execution"],
                "approval": self.workflows[task_id]["approval"],
            }
            for task_id in self.ready_tasks(completed)
        ]
