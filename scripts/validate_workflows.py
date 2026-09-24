from pathlib import Path
import sys
import yaml

WORKFLOW_DIR = Path("workflows/spv_factory")

REQUIRED_FIELDS = {
    "task_id",
    "name",
    "phase",
    "inputs",
    "dependencies",
    "applicability",
    "decision",
    "execution",
    "approval",
    "evidence",
    "completion",
    "escalate_if",
}

VALID_PHASES = {
    "formation",
    "governance",
    "financing",
    "film",
    "accounting",
    "close",
}

VALID_MODES = {"human", "agent"}

VALID_TYPES = {
    "manual",
    "deterministic",
    "api",
    "browser",
    "agent",
}

VALID_APPROVAL_TIMING = {
    "before_execution",
    "before_submission",
    "after_execution",
    "never",
}


def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)


files = sorted(WORKFLOW_DIR.glob("*.yaml"))

if not files:
    fail("No workflow files found.")

tasks = {}

for path in files:
    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:
        fail(f"{path}: invalid YAML: {exc}")

    if not isinstance(data, dict):
        fail(f"{path}: root must be an object.")

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        fail(f"{path}: missing fields: {sorted(missing)}")

    task_id = data["task_id"]

    if task_id in tasks:
        fail(f"Duplicate task_id: {task_id}")

    tasks[task_id] = data

    if data["phase"] not in VALID_PHASES:
        fail(f"{task_id}: invalid phase: {data['phase']}")

    decision = data["decision"]

    if not isinstance(decision, dict):
        fail(f"{task_id}: decision must be an object.")

    if "required" not in decision:
        fail(f"{task_id}: decision.required is missing.")

    if decision["required"]:
        for field in ("authority", "record"):
            if not decision.get(field):
                fail(f"{task_id}: decision.required=true requires {field}.")

    execution = data["execution"]

    if execution["mode"] not in VALID_MODES:
        fail(f"{task_id}: invalid execution.mode.")

    if execution["type"] not in VALID_TYPES:
        fail(f"{task_id}: invalid execution.type.")

    approval = data["approval"]

    if "required" not in approval:
        fail(f"{task_id}: approval.required is missing.")

    if approval["required"]:
        if approval.get("timing") not in VALID_APPROVAL_TIMING:
            fail(f"{task_id}: approval.required=true requires valid timing.")
        if not approval.get("approver"):
            fail(f"{task_id}: approval.required=true requires approver.")

    else:
        if approval.get("timing") not in (None, "never"):
            fail(f"{task_id}: approval.required=false cannot have active timing.")

    if not isinstance(data["dependencies"], list):
        fail(f"{task_id}: dependencies must be a list.")

    applicability = data["applicability"]
    if not isinstance(applicability, dict):
        fail(f"{task_id}: applicability must be an object.")

    if applicability.get("type") not in {"always", "conditional"}:
        fail(f"{task_id}: applicability.type must be always or conditional.")

    if applicability["type"] == "conditional" and not applicability.get("condition"):
        fail(f"{task_id}: conditional applicability requires condition.")


# Validate dependency references.
for task_id, data in tasks.items():
    for dependency in data["dependencies"]:
        if dependency not in tasks:
            fail(
                f"{task_id}: dependency does not exist: {dependency}"
            )


# Detect dependency cycles using DFS.
visiting = set()
visited = set()


def visit(task_id, path):
    if task_id in visiting:
        cycle = " -> ".join(path + [task_id])
        fail(f"Dependency cycle detected: {cycle}")

    if task_id in visited:
        return

    visiting.add(task_id)

    for dependency in tasks[task_id]["dependencies"]:
        visit(dependency, path + [task_id])

    visiting.remove(task_id)
    visited.add(task_id)


for task_id in tasks:
    visit(task_id, [])


print(f"PASS: {len(tasks)} workflow tasks validated.")
print("PASS: all task IDs are unique.")
print("PASS: all dependencies exist.")
print("PASS: no dependency cycles detected.")
print("PASS: schema structure is valid.")
