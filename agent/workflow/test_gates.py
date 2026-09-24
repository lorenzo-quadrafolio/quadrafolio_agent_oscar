from agent.workflow.loader import WorkflowLoader
from agent.workflow.gates import WorkflowGates


def main():
    loader = WorkflowLoader()
    workflows = loader.load_all()

    gates = WorkflowGates(workflows)

    # FORMATION_03 requires a human decision.
    result = gates.evaluate("FORMATION_03")

    print("FORMATION_03 without decision:")
    print(result)

    assert result["status"] == "waiting_for_decision"
    assert result["can_execute"] is False

    # Once the decision is made, the task should be executable
    # because this task does not require approval.
    result = gates.evaluate(
        "FORMATION_03",
        decision_made=True,
    )

    print()
    print("FORMATION_03 after decision:")
    print(result)

    assert result["status"] == "ready_to_execute"
    assert result["can_execute"] is True

    print()
    print("PASS: decision and approval gates work.")


if __name__ == "__main__":
    main()
