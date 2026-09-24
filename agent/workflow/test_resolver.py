from agent.workflow.loader import WorkflowLoader
from agent.workflow.resolver import WorkflowResolver


def main():
    loader = WorkflowLoader()
    workflows = loader.load_all()

    resolver = WorkflowResolver(workflows)

    completed = {
        "FORMATION_01",
        "FORMATION_02",
    }

    ready = resolver.ready_tasks(completed)

    print("Ready task IDs:")
    for task_id in ready:
        print(f"  - {task_id}")

    assert ready == ["FORMATION_03"]

    next_tasks = resolver.next_tasks(completed)

    print()
    print("Next tasks:")

    for task in next_tasks:
        print(f"  {task['task_id']}")
        print(f"    Name: {task['name']}")
        print(f"    Phase: {task['phase']}")
        print(
            f"    Decision required: "
            f"{task['decision']['required']}"
        )
        print(
            f"    Execution: "
            f"{task['execution']['mode']} / "
            f"{task['execution']['type']}"
        )
        print(
            f"    Approval required: "
            f"{task['approval']['required']}"
        )

    assert len(next_tasks) == 1
    assert next_tasks[0]["task_id"] == "FORMATION_03"

    # Test that multiple ready tasks are all returned.
    completed = {
        "FORMATION_01",
        "FORMATION_02",
        "FORMATION_03",
    }

    ready = resolver.ready_tasks(completed)

    print()
    print("Ready after completing FORMATION_03:")

    for task_id in ready:
        print(f"  - {task_id}")

    assert "FORMATION_04" in ready
    assert len(ready) >= 1

    print()
    print("PASS: next-task selection works.")


if __name__ == "__main__":
    main()
