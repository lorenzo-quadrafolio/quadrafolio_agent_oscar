from agent.workflow.loader import WorkflowLoader
from agent.workflow.state import WorkflowState


def main():
    loader = WorkflowLoader()
    workflows = loader.load_all()

    state = WorkflowState(
        workflow_id="film_001_spv_setup"
    )

    state.initialize(list(workflows.keys()))

    print(f"Initialized tasks: {len(state.tasks)}")

    assert len(state.tasks) == 29

    task = state.task("FORMATION_03")

    print()
    print("Initial state:")
    print(task)

    assert task.status == "pending"

    task.set_status("waiting_for_decision")

    print()
    print("After decision gate:")
    print(task)

    assert task.status == "waiting_for_decision"

    task.decision_made = True
    task.set_status("ready")

    print()
    print("After decision:")
    print(task)

    assert task.status == "ready"
    assert task.decision_made is True

    task.set_status("running")

    print()
    print("While running:")
    print(task)

    assert task.status == "running"
    assert task.started_at is not None

    task.set_status("completed")

    print()
    print("After completion:")
    print(task)

    assert task.status == "completed"
    assert task.completed_at is not None

    completed = state.completed_task_ids()

    print()
    print("Completed tasks:")
    print(completed)

    assert completed == {"FORMATION_03"}

    print()
    print("PASS: workflow state works.")


if __name__ == "__main__":
    main()
