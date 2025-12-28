# AGENTS.md

This file defines how automated coding agents (e.g. Codex CLI) should operate in the **spirograph**
repository in its current state (pre–v0→v1 refactor).
The primary goal is to support incremental experimentation without destabilizing existing behavior.

This file is intentionally conservative.

## Current Project State (Important Context)

- This project is an evolving personal prototype / proof-of-concept.
- A v0→v1 refactor is IN PROGRESS and the repo may be mid-transition.
- Existing structure, naming, and flow may not be ideal but should be preserved for now.
- v1 work should be additive and isolated where possible (new v1 modules/files), per the active contract.
- Avoid “cleanups”, reorganizations, or architectural improvements unless explicitly instructed.

## Role of the Agent

The agent acts as an **implementation executor**, not an architect.

- Follow the instructions in the active contract file (for example `codex/contract.md`) exactly.
- Use the active contract file (typically `codex/contract.md`) as the source of execution instructions.
- Do NOT redesign architecture or anticipate future refactors.
- Do NOT attempt to “prepare” the codebase for v1.
- If instructions are unclear or incomplete, stop and ask before making changes.

## Change Discipline (Strict)

- Prefer minimal, localized diffs.
- Do not perform unrelated refactors, reorganizations, or stylistic rewrites.
- Do not rename files, modules, classes, functions, or parameters unless explicitly instructed.
- Do not move code between files unless explicitly instructed.
- Do not change behavior outside the stated scope.
- Touch only the files listed in the contract scope.
- Do not modify architecture_v1.md unless explicitly instructed in the active contract.
  - If additional files are absolutely required, announce them and wait for approval.

## Codebase-Specific Guidance

- Preserve the existing control flow, even if it appears awkward.
- Prefer adding code over restructuring existing code.
- Match the surrounding coding style exactly.
- Avoid introducing new abstractions, base classes, registries, or frameworks.
- Assume Python 3.11+, with its type hint features. Never use `from 
__future__ import annotations`.
- This project is not async and should remain synchronous unless explicitly stated.

## Verification and Execution (Lightweight by Design)

Full automated test coverage is NOT expected at this stage.

The agent should prefer the lightest verification that provides confidence:

- Import/load sanity checks (for example: importing the main module).
- Running the primary entrypoint or CLI if applicable.
- Running a single representative execution path if specified in the contract.

If verification is specified in the contract:
- Run it.
- Fix failures before stopping.

If no verification is specified:
- Do not invent heavy verification steps.
- State clearly what (if anything) was executed to validate behavior.

## When Tests Do Not Exist

This is expected for spirograph at this stage.

- Do NOT introduce a full test framework unless explicitly instructed.
- Micro-tests or tiny assertion scripts are acceptable ONLY if requested.
- Preserve existing behavior unless the contract explicitly changes it.

## Output and Review Requirements

Before stopping, the agent must:

- Summarize the changes made.
- List all files touched.
- Explicitly confirm that no refactors or structural changes were performed.
- Note any assumptions or uncertainties.
- State what verification (if any) was run.

## Safety Rules

- Never delete code unless explicitly instructed.
- Never commit changes; leave all work uncommitted.
- Do not modify git history, tags, branches, or repository configuration.
- Do not add new dependencies unless explicitly instructed.

End of AGENTS.md.