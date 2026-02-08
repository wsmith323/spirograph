# AGENTS Guide

## 1. Purpose
This file is the operational guide for AI/code agents working in this repository. Prioritize behavioral correctness and architectural boundaries over opportunistic refactors or cosmetic rewrites.

## 2. Repo Snapshot
- Python version: `>=3.12` (see `/Users/warren/work/projects/spirograph/pyproject.toml`).
- Entrypoints:
  - `spirograph`
  - `python3 -m spirograph.main`
- Pipeline:
  - `EngineRequest -> CurveGenerator -> GeneratedCurve -> RenderPlanBuilder -> RenderPlan -> CurveRenderer`
- Current renderer: turtle (`TurtleGraphicsRenderer`).

## 3. Architecture Boundaries (Do/Don't)
- `spirograph/cli`: user input, session state, and geometry randomness setup.
- `spirograph/generation`: pure geometry generation, span derivation, and metadata.
- `spirograph/rendering`: render plan construction and drawing.
- `spirograph/orchestration.py`: coordinate pipeline stages only.
- Do not move logic across layers unless explicitly requested.
- Do not add rendering/UI concerns to generation code.
- Do not add geometry/random-parameter logic to renderer code.

## 4. Behavior Invariants (Must Preserve)
- Preserve closure/laps behavior derived from GCD-based period semantics.
- Preserve randomness separation:
  - Geometry randomness in CLI random helpers (`spirograph/cli/random.py`).
  - Color randomness in render-plan construction (`spirograph/rendering/builder.py`).
  - No hidden randomness in generators or renderers.
- Preserve existing color mode semantics:
  - `fixed`, `random_per_run`, `random_per_lap`, `random_every_n_laps`, `random_per_spin`, `random_every_n_spins`.
- Keep both CLI workflows functional:
  - Manual parameter flow.
  - Random generation flow (including locks/evolution modes).

## 5. Key Files
- `/Users/warren/work/projects/spirograph/spirograph/main.py`
- `/Users/warren/work/projects/spirograph/spirograph/orchestration.py`
- `/Users/warren/work/projects/spirograph/spirograph/generation/circular_generator.py`
- `/Users/warren/work/projects/spirograph/spirograph/rendering/builder.py`
- `/Users/warren/work/projects/spirograph/spirograph/rendering/turtle_renderer.py`
- `/Users/warren/work/projects/spirograph/docs/architecture/architecture_v1.md`

## 6. Coding Rules
- Keep type hints modern and explicit.
- Preserve repository style and Ruff configuration in `/Users/warren/work/projects/spirograph/pyproject.toml`.
- Prefer small, focused edits; avoid broad refactors without explicit approval.
- If changing behavior-affecting math, document:
  - Why the change is needed.
  - What remains equivalent.
  - What behavior changes intentionally.

## 7. Validation Checklist for Agents
- Run available static checks/tests when present.
- For Python/test commands, use:
  - `VIRTUAL_ENV=/path/to/venv ./scripts/test ...`
- `VIRTUAL_ENV` is required; do not rely on shell activation state for
  non-interactive runs.
- Minimum manual smoke checks:
  - Launch CLI.
  - Run one random curve.
  - Run one manual curve.
  - Run one non-fixed color mode.
- Confirm no layer-boundary violations were introduced.

## 8. Out-of-Scope by Default
- Persistence/storage systems.
- GUI or web UI.
- Non-circular geometry.
- Major architecture rewrites.
- Any of the above requires explicit request.

## 9. PR/Change Reporting Expectations for Agents
- State exactly what changed.
- State whether behavior invariants were touched.
- List risks/regression potential.
- List what was validated (and what was not).
