from typing import Dict, Any, List

from agent.workflow.loader import WorkflowLoader
from agent.workflow.resolver import WorkflowResolver
from agent.workflow.gates import WorkflowGates
from agent.workflow.state import WorkflowState


class WorkflowEngine:
    """High-level interface for a single workflow instance."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.loader = WorkflowLoader()
        self.workflows = self.loader.load_all()
        self.resolver = WorkflowResolver(self.workflows)
        self.gates = WorkflowGates(self.workflows)
        self.state = WorkflowState(workflow_id=workflow_id)
        self.state.initialize(list(self.workflows.keys()))
        self._refresh_ready_states()

    def task(self, task_id: str) -> Dict[str, Any]:
        return self.loader.load(task_id)

    def task_state(self, task_id: str):
        return self.state.task(task_id)

    def completed_task_ids(self) -> set[str]:
        return self.state.completed_task_ids()

    def ready_tasks(self) -> List[str]:
        self._refresh_ready_states()
        return sorted(
            task_id
            for task_id, task_state in self.state.tasks.items()
            if task_state.status == "ready"
        )

    def blocked_tasks(self) -> Dict[str, List[str]]:
        return self.resolver.blocked_tasks(self.completed_task_ids())

    def next_tasks(self) -> List[Dict[str, Any]]:
        self._refresh_ready_states()
        return [
            {
                "task_id": task_id,
                "name": self.workflows[task_id]["name"],
                "phase": self.workflows[task_id]["phase"],
                "decision": self.workflows[task_id]["decision"],
                "execution": self.workflows[task_id]["execution"],
                "approval": self.workflows[task_id]["approval"],
            }
            for task_id in self.ready_tasks()
        ]

    def status(self) -> Dict[str, Any]:
        self._refresh_ready_states()

        counts = {}
        for task_state in self.state.tasks.values():
            counts[task_state.status] = counts.get(task_state.status, 0) + 1

        ready_tasks = self.ready_tasks()

        return {
            "workflow_id": self.workflow_id,
            "total_tasks": len(self.state.tasks),
            "completed": counts.get("completed", 0),
            "not_applicable": counts.get("not_applicable", 0),
            "ready": len(ready_tasks),
            "waiting_for_applicability": counts.get(
                "waiting_for_applicability", 0
            ),
            "waiting_for_decision": counts.get("waiting_for_decision", 0),
            "waiting_for_approval": counts.get("waiting_for_approval", 0),
            "running": counts.get("running", 0),
            "blocked": counts.get("blocked", 0),
            "failed": counts.get("failed", 0),
            "ready_tasks": ready_tasks,
        }

    def determine_applicability(
        self,
        task_id: str,
        applicable: bool,
    ) -> Dict[str, Any]:
        task = self.task(task_id)
        task_state = self.task_state(task_id)

        applicability = task["applicability"]

        if applicability["type"] != "conditional":
            raise ValueError(
                f"{task_id} is not a conditional task."
            )

        if task_state.status in {"completed", "not_applicable", "running"}:
            raise ValueError(
                f"{task_id} cannot have applicability changed from "
                f"status '{task_state.status}'."
            )

        blockers = self.resolver.blockers(
            task_id,
            self.completed_task_ids(),
        )

        if blockers:
            return {
                "status": "blocked",
                "can_execute": False,
                "reason": "Task dependencies are incomplete.",
                "blockers": blockers,
            }

        task_state.applicable = applicable

        if not applicable:
            task_state.set_status("not_applicable")
            self._refresh_ready_states()

            return {
                "status": "not_applicable",
                "can_execute": False,
                "reason": "Task determined not applicable.",
            }

        self._refresh_task_state(task_id)

        return {
            "status": task_state.status,
            "can_execute": task_state.status == "ready",
            "reason": None,
        }

    def decide(
        self,
        task_id: str,
        approved: bool = True,
    ) -> Dict[str, Any]:
        task = self.task(task_id)
        task_state = self.task_state(task_id)

        if task_state.status == "not_applicable":
            raise ValueError(
                f"{task_id} is not applicable."
            )

        if not task["decision"]["required"]:
            raise ValueError(
                f"{task_id} does not require a decision."
            )

        if task_state.status == "completed":
            raise ValueError(
                f"{task_id} is already completed."
            )

        if not approved:
            task_state.error = "Human decision rejected."
            task_state.set_status("failed")
            return {
                "status": "failed",
                "reason": "Human decision rejected.",
            }

        task_state.decision_made = True
        self._refresh_task_state(task_id)

        return {
            "status": task_state.status,
            "can_execute": task_state.status == "ready",
        }

    def approve(
        self,
        task_id: str,
        granted: bool = True,
    ) -> Dict[str, Any]:
        task = self.task(task_id)
        task_state = self.task_state(task_id)

        if task_state.status == "not_applicable":
            raise ValueError(
                f"{task_id} is not applicable."
            )

        if not task["approval"]["required"]:
            raise ValueError(
                f"{task_id} does not require approval."
            )

        if not granted:
            task_state.error = "Approval rejected."
            task_state.set_status("failed")
            return {
                "status": "failed",
                "reason": "Approval rejected.",
            }

        task_state.approval_granted = True
        self._refresh_task_state(task_id)

        return {
            "status": task_state.status,
            "can_execute": task_state.status == "ready",
        }

    def start(self, task_id: str) -> Dict[str, Any]:
        task_state = self.task_state(task_id)

        if task_state.status == "completed":
            raise ValueError(
                f"{task_id} is already completed."
            )

        if task_state.status == "not_applicable":
            raise ValueError(
                f"{task_id} is not applicable."
            )

        if (
            self.workflows[task_id]["applicability"]["type"] == "conditional"
            and task_state.applicable is None
        ):
            return {
                "status": "waiting_for_applicability",
                "can_execute": False,
                "reason": "Applicability decision required.",
            }

        completed = self.completed_task_ids()

        blockers = self.resolver.blockers(task_id, completed)

        if blockers:
            return {
                "status": "blocked",
                "can_execute": False,
                "reason": "Task dependencies are incomplete.",
                "blockers": blockers,
            }

        result = self.gates.evaluate(
            task_id,
            decision_made=task_state.decision_made,
            approval_granted=task_state.approval_granted,
        )

        if not result["can_execute"]:
            return result

        task_state.set_status("running")

        return {
            "status": "running",
            "can_execute": True,
            "reason": None,
        }

    def complete(self, task_id: str) -> Dict[str, Any]:
        task_state = self.task_state(task_id)

        if task_state.status != "running":
            raise ValueError(
                f"{task_id} cannot be completed from status "
                f"'{task_state.status}'."
            )

        task_state.set_status("completed")
        self._refresh_ready_states()

        return {
            "status": "completed",
            "can_execute": False,
        }

    def _refresh_ready_states(self) -> None:
        completed = self.completed_task_ids()

        for task_id, task_state in self.state.tasks.items():

            if task_state.status in {
                "completed",
                "not_applicable",
                "running",
                "failed",
                "waiting_for_applicability",
                "waiting_for_decision",
                "waiting_for_approval",
            }:
                continue

            blockers = self.resolver.blockers(
                task_id,
                completed,
            )

            if blockers:
                task_state.set_status("blocked")
                continue

            task = self.workflows[task_id]

            if (
                task["applicability"]["type"] == "conditional"
                and task_state.applicable is None
            ):
                task_state.set_status("waiting_for_applicability")
                continue

            if task["decision"]["required"]:
                if not task_state.decision_made:
                    task_state.set_status("waiting_for_decision")
                    continue

            if task["approval"]["required"]:
                if not task_state.approval_granted:
                    task_state.set_status("waiting_for_approval")
                    continue

            task_state.set_status("ready")

    def _refresh_task_state(self, task_id: str) -> None:
        task_state = self.task_state(task_id)

        if task_state.status in {
            "completed",
            "not_applicable",
            "running",
            "failed",
        }:
            return

        completed = self.completed_task_ids()

        blockers = self.resolver.blockers(
            task_id,
            completed,
        )

        if blockers:
            task_state.set_status("blocked")
            return

        task = self.workflows[task_id]

        if (
            task["applicability"]["type"] == "conditional"
            and task_state.applicable is None
        ):
            task_state.set_status("waiting_for_applicability")
            return

        if task["decision"]["required"] and not task_state.decision_made:
            task_state.set_status("waiting_for_decision")
            return

        if task["approval"]["required"] and not task_state.approval_granted:
            task_state.set_status("waiting_for_approval")
            return

        task_state.set_status("ready")
