from agent.workflow.loader import WorkflowLoader


def main():
    loader = WorkflowLoader()

    workflows = loader.load_all()

    print(f"Loaded {len(workflows)} workflow tasks.")

    assert len(workflows) == 29
    assert "FORMATION_01" in workflows
    assert "FINANCING_01" in workflows
    assert "CLOSE_04" in workflows
    assert "FORMATION_07" in workflows

    task = loader.load("FORMATION_03")

    print(f"Loaded task: {task['task_id']}")
    print(f"Name: {task['name']}")
    print(f"Phase: {task['phase']}")
    print(f"Dependencies: {task['dependencies']}")

    print("PASS: workflow loader works.")


if __name__ == "__main__":
    main()
