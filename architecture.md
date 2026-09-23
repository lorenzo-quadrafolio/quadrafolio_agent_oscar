# Quadrafolio Agent — Architecture

Version: 0.1
Status: Draft

## 1. Purpose

The Quadrafolio Agent is a company-wide AI operating layer.

It allows employees to:
- Ask questions.
- Search company knowledge.
- Investigate problems.
- Perform operational tasks.
- Work with code and files.
- Run long-running workflows.
- Create and manage film SPVs.
- Request human approval when required.

The system separates:
- Interface
- Control
- Business state
- Execution state
- Execution
- Human authority

## 2. System architecture

```text
Slack
  ↓
Agent Gateway
  ↓
Orchestrator
  ↓
CrewAI Flows / Deterministic tools and APIs
  ↓
Workers
  ↓
Evidence
  ↓
Notion + Postgres
Slack

Slack is the primary human interface.

Slack handles:

User requests
Results
Progress
Approval requests
Errors
Follow-up questions

Slack does not contain workflow logic.

Agent Gateway

The Agent Gateway sits between Slack and the agent system.

Responsibilities:

Authenticate the user.
Identify the Slack channel and thread.
Load user permissions.
Attach relevant context.
Normalize requests.
Handle approval interactions.
Format responses for Slack.

The Gateway does not decide how a workflow should execute.

Orchestrator

The Orchestrator is the control plane.

It determines:

User intent
Applicable workflow
Target entity
Current state
Dependencies
Next task
Required permissions
Worker selection
Approval requirements
Evidence validation

The Orchestrator owns control, not business truth.

CrewAI

CrewAI is used primarily for long-running and stateful workflows.

Examples:

SPV creation
Employee onboarding
Complex research
Multi-step operational processes

CrewAI Flows are the default abstraction for these workflows.

CrewAI does not own company business state.

Deterministic tools and APIs

Use deterministic integrations whenever possible.

Examples:

Notion API
GitHub API
Google APIs
Slack API
Database queries
Internal APIs
File operations

Preferred execution order:

Direct API
    ↓
MCP / structured tool
    ↓
Browser automation
    ↓
Computer-use agent

If an API can reliably perform an action, do not use browser automation for the same action.

Workers

Workers perform individual tasks.

Examples:

Claude Code
Codex
Hermes
Browser worker
Python execution
Internal services
Direct APIs

Workers are replaceable.

The Orchestrator should not depend on a specific worker.

3. Data ownership
Notion — business truth

Notion is the source of truth for operational and business information.

Examples:

Films
SPVs
SPV tasks
Project status
Ownership information
Financing information
Company documentation
Decisions
Business knowledge
Postgres — execution truth

Postgres stores agent execution state.

Examples:

Jobs
Workflow runs
Tasks
Worker assignments
Attempts
Errors
Approval requests
Execution IDs
Timestamps
Evidence references

Example fields:

job_id
workflow_id
task_id
worker
status
attempt
started_at
finished_at
approval_id
execution_id
error

Postgres should not become a duplicate database of company business information.

Files — evidence

Files contain artifacts produced or collected by workflows.

Examples:

Signed documents
Filing confirmations
Contracts
Reports
Screenshots
Generated documents
Financial files

The system should reference evidence rather than relying on an agent's claim that something happened.

4. Request lifecycle
User request
    ↓
Agent Gateway
    ↓
Authentication + permissions
    ↓
Request normalization
    ↓
Intent classification
    ↓
Load business state
    ↓
Select workflow
    ↓
Check dependencies
    ↓
Check permissions
    ↓
Dispatch task
    ↓
Worker executes
    ↓
Worker returns result + evidence
    ↓
Validate evidence
    ↓
Update business state
    ↓
Update execution state
    ↓
Select next task
    ↓
Complete workflow

Workflows must be resumable.

If human input or approval is required, execution pauses without losing state.

5. Permission model
Level 0 — Read

The agent may:

Search
Read
Retrieve
Inspect

No state changes.

Level 1 — Analyse

The agent may:

Analyse
Compare
Calculate
Identify inconsistencies
Produce analysis for human review

No external state changes.

Level 2 — Prepare

The agent may prepare actions.

Examples:

Draft contracts
Prepare filings
Prepare GitHub PRs
Prepare documents
Draft communications

Preparation does not imply authorization to execute.

Level 3 — Execute

The agent may perform explicitly permitted actions.

Examples:

Create Notion pages
Create GitHub branches
Update approved database fields
Perform approved operational actions
Level 4 — Human authority

These actions require human authority:

Sign contracts
Approve ownership
Approve securities terms
Submit legally consequential filings
Move company funds
Approve financing
Approve material rights changes

The agent may prepare these actions but does not independently exercise the authority.

Prohibited

The agent must not:

Sign contracts
Move company funds
Decide ownership
Decide investor economics
Make legal representations on behalf of Quadrafolio
Override human approval
Circumvent permissions
Fabricate evidence
Mark tasks complete without satisfying completion criteria
6. Worker contract

Every worker receives a standard task.

Input
{
  "job_id": "job_123",
  "task_id": "FORMATION_05",
  "instructions": {},
  "inputs": {},
  "permissions": [],
  "required_evidence": []
}
Output
{
  "status": "EXECUTED",
  "result": {},
  "evidence": [],
  "approval_required": false,
  "error": null
}

Possible statuses:

SUCCESS
WAITING_FOR_INPUT
WAITING_FOR_APPROVAL
FAILED
BLOCKED

A worker must not report success without the required evidence.

7. Approval model

Approval is a first-class system object.

An approval request contains:

Action
Reason approval is required
Expected effect
Supporting information
Evidence
Requesting user
Authorized approver

Approval decisions must be recorded.

8. Error and retry model
Retryable

Examples:

Temporary API failure
Browser timeout
Network failure
Rate limit
Worker crash

These may be retried automatically.

Non-retryable

Examples:

Missing information
Conflicting ownership data
Invalid legal entity
Unexpected filing requirement
Permission failure
Human decision required

These move the task to:

WAITING_FOR_INPUT

or:

WAITING_FOR_APPROVAL

or:

BLOCKED

The agent must not repeatedly retry a task when the underlying problem requires human intervention.

9. Non-goals

The initial system is not intended to:

Replace legal counsel.
Replace financial authority.
Replace human approval.
Make autonomous corporate decisions.
Become a single giant "do anything" agent.
Store all company information inside the agent.
Depend on one AI model.
Depend on one worker.
Use browser automation when a reliable API exists.
Rebuild the existing SPV Factory in code.

The existing Notion SPV Factory remains the business workflow and operating system.

The agent system executes and enforces that system.

10. SPV Factory integration

The SPV Factory is the first domain workflow implemented on this architecture.

The existing human-readable SPV Setup Process will be converted into machine-readable task definitions.

Example:

task_id: FORMATION_05

name: Form project LLC

inputs:
  - approved_spv_name
  - state
  - registered_agent
  - principal_address

dependencies:
  - FORMATION_01
  - FORMATION_02
  - FORMATION_03
  - FORMATION_04

execution:
  type: browser
  worker: browser_worker

approval:
  required: true
  timing: before_submission

evidence:
  - articles_of_organization
  - filing_confirmation

completion:
  - filing_confirmation_exists
  - legal_name_matches
  - state_matches

escalate_if:
  - name_unavailable
  - information_conflict
  - unexpected_requirement

The machine-readable workflow becomes executable by the Orchestrator.

The existing Notion workflow remains the human-readable operating manual.

11. Core architectural principles
Prefer deterministic execution over probabilistic execution.
Prefer APIs over browser automation.
Prefer explicit workflows over agent improvisation.
Prefer structured state over conversation history.
Prefer evidence over agent claims.
Prefer human approval over autonomous authority.
Keep workers replaceable.
Keep business state separate from execution state.
Never silently bypass a permission or approval requirement.
Never mark a task complete without satisfying its completion criteria.

The goal is not maximum autonomy.

The goal is reliable, observable, controllable and auditable execution.
