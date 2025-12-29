# AGENTS.md

This file defines how automated coding agents (e.g., Codex CLI) should operate in the **spirograph** repository during the v1 architectural consolidation phase.

## Current Project State (v1 Refactor)

- The project has successfully transitioned to a v1 pipeline-based architecture (Request → Generator → Builder → Renderer).
- The "v0" code has been moved to `v0_main.py` for reference and parity verification.
- The focus is now on achieving full feature parity (Epitrochoids, advanced color modes, evolution logic) within the v1 structure.
- **architecture_v1.md** is the locked ground truth for all structural decisions.

## Role of the Agent

The agent acts as a **v1 implementation executor**.

- Follow the instructions in the active contract file (typically `codex/contract.md`) exactly.
- Use `architecture_v1.md` to resolve any ambiguity regarding responsibility boundaries.
- Do NOT regress the architecture to v0 procedural styles.
- Do NOT perform unrelated "cleanups" or refactors outside the contract scope.

## Change Discipline (Strict)

- **Pipelines only**: All new features must be implemented as part of the v1 pipeline stages.
- **Isolated Diffs**: Prefer adding new methods or files over modifying established v1 core interfaces unless explicitly instructed.
- **No Side Effects**: Core domain logic (Generators, Builders) must remain stateless and pure.
- **Touch only the files listed in the contract scope.**
- Do not modify `architecture_v1.md` or `AGENTS.md` unless explicitly instructed in an active contract.

## Codebase-Specific Guidance

- **Type Safety**: Use Python 3.11+ type hints for all new code. Never use `from __future__ import annotations`.
- **Statelessness**: Generators must never store state. CLI Session State is the only place for "evolution" or "memory" between runs.
- **Decoupling**: The Renderer must never know about geometry; the Generator must never know about colors.
- **Color Primitive**: Use the v1 `Color` value object (with `r, g, b, a` attributes) for all path representations.

## Verification and Execution

- **Sanity Checks**: Always perform import/load checks.
- **Functional Check**: Run the main v1 entry point (`python3 -m spirograph.main`) to verify the integrated pipeline if the contract involves CLI changes.
- **Parity Check**: If a feature is ported from v0, verify it behaves identically to the version in `v0_main.py`.

## Output and Review Requirements

Before stopping, the agent must:
- Summarize the v1 components modified or created.
- Confirm adherence to the `architecture_v1.md` responsibility boundaries.
- State clearly what verification steps were performed.

## Safety Rules

- Never delete v0 reference code (`v0_main.py`) unless explicitly instructed.
- Never commit changes; leave work uncommitted for review.
- Do not add new external dependencies without approval.

End of AGENTS.md.