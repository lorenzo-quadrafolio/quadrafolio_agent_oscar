from agent.workflow.engine import WorkflowEngine


def main():
    engine = WorkflowEngine("film_001_spv_setup")

    print("=== INITIAL STATE ===")
    print(engine.task_state("FORMATION_01"))

    print("\n=== INITIAL NEXT TASKS ===")
    for task in engine.next_tasks():
        print(f"{task['task_id']}: {task['name']}")

    assert engine.task_state("FORMATION_01").status == "ready"
    assert engine.task_state("FORMATION_03").status == "blocked"

    print("\n=== COMPLETE BOOTSTRAP TASKS ===")

    engine.start("FORMATION_01")
    engine.complete("FORMATION_01")

    engine.start("FORMATION_02")
    engine.complete("FORMATION_02")

    print("FORMATION_01: completed")
    print("FORMATION_02: completed")

    print("\n=== FORMATION_03 STATE ===")
    print(engine.task_state("FORMATION_03"))

    assert engine.task_state("FORMATION_03").status == "waiting_for_decision"

    print("\n=== MAKE DECISION ===")

    result = engine.decide("FORMATION_03", approved=True)
    print(result)

    assert result["status"] == "ready"

    print("\n=== START TASK ===")

    result = engine.start("FORMATION_03")
    print(result)

    assert result["status"] == "running"

    print("\n=== COMPLETE TASK ===")

    result = engine.complete("FORMATION_03")
    print(result)

    assert result["status"] == "completed"

    print("\n=== WORKFLOW STATUS ===")

    status = engine.status()
    print(f"Workflow: {status['workflow_id']}")
    print(f"Total tasks: {status['total_tasks']}")
    print(f"Completed: {status['completed']}")
    print(f"Ready: {status['ready']}")
    print(f"Waiting for decision: {status['waiting_for_decision']}")
    print(f"Waiting for approval: {status['waiting_for_approval']}")
    print(f"Running: {status['running']}")
    print(f"Blocked: {status['blocked']}")
    print(f"Failed: {status['failed']}")
    print(f"Ready tasks: {status['ready_tasks']}")

    assert status["total_tasks"] == 29
    assert status["completed"] == 3
    assert status["waiting_for_decision"] == 2
    assert status["ready"] == 0

    print("\n=== CONDITIONAL TASK ===")

    financing_task = engine.task_state("FINANCING_03")
    print(financing_task)

    assert financing_task.status == "blocked"

    print("\nPASS: 29-task workflow baseline is correct.")


if __name__ == "__main__":
    main()


def test_blocked_task_precedes_approval_gate():
    engine = WorkflowEngine("blocked_gate_test")

    result = engine.start("FINANCING_03")

    assert result["status"] == "blocked"
    assert result["can_execute"] is False
    assert result["blockers"]

    print("=== BLOCKED VS APPROVAL TEST ===")
    print(result)
    print("PASS: dependency blockers take precedence over approval gates.")


def test_conditional_not_applicable():
    engine = WorkflowEngine("conditional_test")

    # Complete the dependencies required by FINANCING_03.
    for task_id in [
        "FORMATION_01",
        "FORMATION_02",
        "FORMATION_03",
        "FORMATION_04",
        "FORMATION_05",
        "FORMATION_06",
        "GOVERNANCE_02",
        "FINANCING_01",
        "GOVERNANCE_03",
    ]:
        state = engine.task_state(task_id)

        if state.status == "waiting_for_decision":
            engine.decide(task_id)

        if state.status == "waiting_for_approval":
            engine.approve(task_id)

        engine.start(task_id)
        engine.complete(task_id)

    financing_state = engine.task_state("FINANCING_03")

    assert financing_state.status == "waiting_for_applicability"

    print("\n=== CONDITIONAL N/A TEST ===")
    print(financing_state)

    result = engine.determine_applicability(
        "FINANCING_03",
        applicable=False,
    )

    print(result)

    assert result["status"] == "not_applicable"
    assert engine.task_state("FINANCING_03").status == "not_applicable"
    assert "FINANCING_03" in engine.completed_task_ids()

    print("PASS: conditional task can be explicitly marked N/A.")
    print("PASS: N/A satisfies dependency resolution.")


if __name__ == "__main__":
    main()
    test_conditional_not_applicable()
