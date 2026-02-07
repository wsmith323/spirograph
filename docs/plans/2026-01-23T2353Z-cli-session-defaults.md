Plan-ID: 2026-01-23T2353Z-cli-session-defaults
Status: approved

Intent:
- Problem
  - The CLI session starts with hardcoded initial defaults (e.g., color mode and related settings) in code, and we want to change those initial defaults in a controlled, reviewable way.
- Goals
  - Update the initial `CliSessionState` defaults so new CLI sessions start with `ColorMode.RANDOM_EVERY_N_SPINS`.
  - Set the default `spins_per_color` to 10 for new sessions.
- Non-goals
  - Do not add command-line flags, config files, or persistence of settings between runs.
  - Do not change rendering behavior, random generation logic/ranges, or any non-default runtime behavior after startup.
  - Do not refactor the CLI or move to a different CLI framework.
- Chosen approach
  - Edit `spirograph/cli/session.py` to change the default values on the `CliSessionState` dataclass fields (`color_mode`, `spins_per_color`) and leave everything else untouched.
- Risks and open questions
  - None significant; change is localized. Primary risk is user expectation mismatch if they rely on the previous initial color defaults.
- Decisions
  - Change only startup defaults in `CliSessionState`, not per-run logic or prompts.
  - Keep the change minimal and scoped to a single file.

Scope:
- file: spirograph/cli/session.py
  intent: Update `CliSessionState` startup defaults for `color_mode` and `spins_per_color`.

Constraints:
- Only modify files listed in Scope during execution.
- No new CLI flags, config layers, or persistence mechanisms.
- No changes to rendering, generation, or prompt behavior beyond the initial defaults.

Validation:
- python3 -c "from spirograph.cli.session import CliSessionState; from spirograph.rendering.types import ColorMode; s=CliSessionState(); assert s.color_mode is ColorMode.RANDOM_EVERY_N_SPINS; assert s.spins_per_color == 10"
- python3 -m compileall spirograph

