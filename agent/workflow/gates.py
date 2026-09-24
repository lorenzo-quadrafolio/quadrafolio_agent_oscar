from typing import Dict, Any


class WorkflowGates:
    """Evaluate decision and approval requirements for workflow tasks."""

    def __init__(self, workflows: Dict[str, Dict[str, Any]]):
        self.workflows = workflows

    def evaluate(
        self,
        task_id: str,
        decision_made: bool = False,
        approval_granted: bool = False,
    ) -> Dict[str, Any]:
        """Return the execution state imposed by the task's gates."""

        task = self.workflows[task_id]

        decision = task["decision"]
        approval = task["approval"]

        if decision["required"] and not decision_made:
            return {
                "status": "waiting_for_decision",
                "can_execute": False,
                "reason": "Human decision required.",
            }

        if approval["required"] and not approval_granted:
            return {
                "status": "waiting_for_approval",
                "can_execute": False,
                "reason": (
                    f"Approval required "
                    f"{approval['timing']}."
                ),
            }

        return {
            "status": "ready_to_execute",
            "can_execute": True,
            "reason": None,
        }
