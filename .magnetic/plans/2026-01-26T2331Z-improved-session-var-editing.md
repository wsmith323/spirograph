Plan-ID: 2026-01-26T2331Z-improved-session-var-editing
Status: approved

Intent:
- Problem
  - The CLI’s session settings (“session vars”) are currently edited via a single `e` flow that forces the user through every prompt in sequence, even when they only want to change one setting.
  - Some session vars have type/UX mismatches (notably `line_width` is a `float` but is edited as an `int`), making precise edits awkward or impossible.
- Goals
  - Provide improved session var editing as an interactive **submenu** so users can edit one setting (or category) at a time and return to the menu until done.
  - Preserve the current “press Enter keeps the current value” default behavior for prompts.
  - Keep existing conditional behavior for color-related settings (only ask for `color`, `laps_per_color`, or `spins_per_color` when relevant to the chosen `color_mode`).
  - Fix the `line_width` editing UX to support non-integer widths (consistent with its `float` type).
- Non-goals
  - No persistence of session settings across runs (no config files, no save/restore).
  - No new CLI framework or broad refactor of the overall main loop beyond the session-edit experience.
  - No changes to rendering/generation behavior beyond how session variables are edited.
  - No “command-style” `set <key> <value>` interface (submenu only).
- Chosen approach
  - Replace/augment the existing `edit_session_settings()` flow in `spirograph/main.py` with a looped submenu that:
    - Shows current session settings (reuse `print_session_status()`).
    - Lets the user choose a category/setting to edit (Geometry/Random/Color/Drawing/Locks).
    - Calls the existing prompt helpers for the chosen setting, using current values as defaults.
    - Returns to the submenu until the user exits back to the main menu.
  - Adjust prompting for `line_width` to accept a positive float instead of forcing an integer.
- Risks and open questions
  - Risk: Changing the semantics of `e` may surprise users accustomed to the old “walk through everything” flow.
  - Risk: Additional branching paths increase chances of missing an edge case (e.g., switching `color_mode` should ensure the appropriate dependent value is editable/relevant).
  - Open question: Should Locks remain a separate main-menu command (`l`) as well as being accessible from the session submenu, or only one entry point?
- Decisions
  - Use a submenu-based session editor (not `set` commands).
  - Keep “Enter keeps current value” semantics; no explicit cancel/back tokens.
  - Ensure `line_width` can be edited as a float and remains positive.
  - Keep changes localized to the CLI code paths that manage session editing and prompting.

Scope:
- file: spirograph/main.py
  intent: Replace `e` (“Edit Session settings”) with a submenu loop that edits one session var at a time and returns to the session menu until exit; keep Locks editing only via the main-menu `l` command.
- file: spirograph/cli/prompts.py
  intent: Add or adapt a prompt helper to edit `line_width` as a positive float (defaulting to current value), and use it from the session submenu.

Constraints:
- Only modify files listed in Scope during execution.
- Do not add persistence, config layers, or CLI flags.
- Do not change generation/rendering behavior beyond editing UX and `line_width` value parsing.
- Locks must remain accessible only from the main menu (`l`) and must not be included in the session-settings submenu.

Validation:
- python3 -m compileall spirograph
- python3 -c "from spirograph.cli.session import CliSessionState; s=CliSessionState(); assert isinstance(s.line_width, float)"
- Manual smoke test: `python3 -m spirograph.main` and verify:
  - `e` opens a submenu and allows editing a single setting without stepping through all prompts.
  - `l` remains the only entry point for Locks.
  - `line_width` accepts a positive float (e.g., `0.5`) and persists in the printed session status.

