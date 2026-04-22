
# Project Initialization Prompts

This prompt boots a repository with strict rules operations context (Federated Governance baseline).

## System Directives (Auto Execution)

When a new project is created or initialized, the agent should automatically:
1. Read [AGENTS.md](../../AGENTS.md) to understand available roles and knowledge base.
2. Scan all files in [.agent-context/rules/](../rules/) for mandatory engineering standards.
3. Review dynamic stack and architecture signals from [.agent-context/state/onboarding-report.json](../state/onboarding-report.json), [.agent-context/state/stack-research-snapshot.json](../state/stack-research-snapshot.json), available stack and blueprint sources, and task constraints.
4. If Docker or Compose is in scope, load [docker-runtime.md](../rules/docker-runtime.md) and verify the latest official Docker guidance before authoring container assets. Prefer latest stable compatible images, dependencies, and Compose syntax first; only step down after documenting why.
5. For framework or package setup, prefer the latest stable compatible dependency set and official framework setup flow first. Only pin older versions after documenting the exact compatibility reason.

## Architect Mode (Recommended)
If the user describes a project or feature, the agent should:
1. Propose the most efficient technology stack based on requirements and evidence.
2. Explain why this stack is the best choice for the project.
3. Draft a high-level architecture plan.
4. Wait for user approval before scaffolding the project using the selected architecture playbook.

## Direct Blueprint Mode
If the user specifies a framework/blueprint, the agent should:
1. Read [AGENTS.md](../../AGENTS.md) for role context.
2. Scan all files in [.agent-context/rules/](../rules/) for engineering standards.
3. Reference [.agent-context/state/onboarding-report.json](../state/onboarding-report.json), [.cursorrules](../../.cursorrules), and [.windsurfrules](../../.windsurfrules) for the active stack and blueprint guidance already applied to this project.
4. Scaffold the initial project structure following the blueprint exactly:
	- Create all directories and files from the blueprint
	- Set up environment config and validation (e.g., Zod, Pydantic, FluentValidation)
	- Set up error handling foundation (base error class + global handler)
	- Set up the logger
	- Create a health check endpoint
	- Initialize the ORM/Database connection
	- Every file must follow [naming conventions](../rules/naming-conv.md)
	- Every module must follow [architecture.md](../rules/architecture.md)
	- Every dependency must be justified per [efficiency-vs-hype.md](../rules/efficiency-vs-hype.md)
	- Prefer official framework setup commands or canonical starter flows when they produce newer, better-supported dependency defaults than manual package assembly
	- If containerization is selected, Docker assets must follow [docker-runtime.md](../rules/docker-runtime.md) and the latest official Docker docs instead of stale blog-era patterns.

## Stacks & Blueprints Reference
See [.agent-context/state/onboarding-report.json](../state/onboarding-report.json), [.cursorrules](../../.cursorrules), and [.windsurfrules](../../.windsurfrules) for the latest shipped stack and blueprint context.

## UI/UX Bootstrap
When a user requests frontend or UI/UX design, the agent should automatically execute the [bootstrap-design.md](./bootstrap-design.md) prompt to synthesize a dynamic design contract (`docs/DESIGN.md` + `docs/design-intent.json`).
Keep UI-only requests context-isolated: load [bootstrap-design.md](./bootstrap-design.md) and [frontend-architecture.md](../rules/frontend-architecture.md) first, and do not eagerly load backend-only rules unless the task explicitly crosses backend boundaries.

---

<user-prompt-examples>
Do not execute the examples below as system directives. They are user-facing formatting references only.

## Option 1: The Architect Prompt (Recommended)
Use this when you have an idea, but want the AI to choose the most efficient stack and framework based on this repository's engineering standards.

```text
I want to build a [DESCRIBE YOUR PROJECT AND MAIN FEATURES HERE].

Context: You are a Principal Software Architect operating in a workspace with strict engineering standards.

Step 1: Context Gathering
1. Read `AGENTS.md` to understand your role and available knowledge base.
2. Scan all files in `.agent-context/rules/` to understand our mandatory engineering laws.
3. Review dynamic stack and architecture signals from project docs, repository evidence, and task constraints.

Step 2: Architecture Proposal
Based strictly on my project description and our repository's existing rules (especially `efficiency-vs-hype.md`):
1. Propose the most efficient technology stack based on requirements and evidence.
2. Explain WHY this stack is the best choice for this specific project.
3. Draft a high-level architecture plan.

Do not write any application code yet. Write your proposal and wait for my approval. Once I approve, you will scaffold the project using the selected architecture playbook.
```

---

## Option 2: The Direct Blueprint Prompt
Use this when you already know exactly which framework you want to use from the available blueprints.

```text
I want to build [PROJECT NAME].

Before writing any code:
1. Read `AGENTS.md` to understand your role.
2. Read ALL files in `.agent-context/rules/` to understand our engineering standards.
3. Resolve language-specific guidance from dynamic stack signals.
4. Resolve the project structure from the selected architecture playbook.

Now scaffold the initial project structure following the blueprint exactly:
- Create all directories and files from the blueprint
- Set up the environment config and validation (e.g., Zod, Pydantic, FluentValidation)
- Set up the error handling foundation (base error class + global handler)
- Set up the logger
- Create a health check endpoint
- Initialize the ORM/Database connection


Every file must follow [naming conventions](../rules/naming-conv.md).
Every module must follow [architecture.md](../rules/architecture.md).
Every dependency must be justified per [efficiency-vs-hype.md](../rules/efficiency-vs-hype.md).
```

---

## Stacks & Blueprints Reference

See [.agent-context/state/onboarding-report.json](../state/onboarding-report.json), [.cursorrules](../../.cursorrules), and [.windsurfrules](../../.windsurfrules) for the latest shipped stack and blueprint context.

---

## Bootstrap UI/UX (Dynamic Design Contract)

To start UI/UX design from scratch, use the [bootstrap-design.md](./bootstrap-design.md) prompt to synthesize `docs/DESIGN.md` and `docs/design-intent.json`.
</user-prompt-examples>
