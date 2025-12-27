

# AGENTS.md

This file defines how automated coding agents (e.g. Codex CLI) should operate in this repository.
It is intended to reduce drift, prevent surprise refactors, and make agent-driven changes easy to
review and verify.

## Role of the Agent

The agent acts as an implementation executor, not an architect.

- Follow the instructions in the active contract file (for example `codex/contract.md`) exactly.
- Do not reinterpret goals or redesign architecture.
- When in doubt, stop and ask for clarification before making changes.

## Change Discipline

- Prefer minimal, targeted diffs.
- Do not perform unrelated refactors, cleanups, or stylistic rewrites.
- Do not rename public APIs, classes, functions, or files unless explicitly instructed.
- Do not change behavior outside the stated scope.
- Touch only the files listed in the contract scope unless absolutely required.
  - If additional files are required, announce them before modifying.

## Project Conventions

- Follow existing patterns and structure already present in the codebase.
- Match the surrounding style and idioms rather than introducing new ones.
- Do not introduce new frameworks, libraries, or abstractions unless explicitly instructed.
- Assume Python 3.11+.

## Verification and Execution

- The agent is expected to run verification commands locally as part of its work.
- Typical verification may include (depending on project state):
  - Linting or formatting checks (for example ruff or black)
  - Import/load sanity checks
  - Test execution if tests exist
  - A defined smoke command or entrypoint
- If a verification step fails, fix the failure before stopping.
- Do not declare work complete until verification passes.

## When Tests Do Not Exist

For proof-of-concept or rapidly evolving code:

- Prefer lightweight verification over full test suites.
- Use import checks, simple execution paths, or small assertion scripts where available.
- Preserve behavior unless the contract explicitly changes it.
- Keep changes tightly scoped to reduce review burden.

## Output and Review

Before stopping, the agent must:

- Summarize the changes made.
- List all files touched.
- Note any assumptions, limitations, or areas of uncertainty.
- Clearly state which verification steps were run and their outcomes.

## Safety Rules

- Never delete data, migrations, or large sections of code unless explicitly instructed.
- Never commit changes; leave all work uncommitted.
- Do not modify git history or repository configuration.

End of AGENTS.md.