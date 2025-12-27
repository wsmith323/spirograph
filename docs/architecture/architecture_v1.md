# Spirograph v1 Architecture

## 1. Purpose and Scope

### Purpose
Spirograph v1 is a ground-up architectural refactor of the existing v0 program.

Its goals are:

- Preserve functional behavior parity with v0 (same geometry, same randomness semantics).
- Dramatically improve architectural extensibility to support future features with minimal ripple.
- Reduce cognitive load as complexity increases by favoring:
  - Separation of concerns
  - Composition over inheritance
  - Clear responsibility boundaries

### Scope of v1 (MVP)
- Stateless execution
- CLI-driven interaction
- Turtle-based rendering
- Circular spirograph geometry only
- Randomized and manually entered inputs (as in v0)

### Explicit Non-Goals for v1
- Persistence (database, file storage)
- GUI or web UI
- Non-circular tracks or rollers
- Exact cross-version reproducibility guarantees

These are intentionally deferred, but architectural hooks for them must exist.

---

## 2. High-Level Conceptual Model

At a high level, v1 is a pipeline:

EngineRequest  
→ CurveGenerator  
→ GeneratedCurve (points + spans + metadata)  
→ RenderPlanBuilder  
→ RenderPlan  
→ CurveRenderer

An Orchestrator coordinates this pipeline but owns no domain logic itself.

---

## 3. Core Architectural Concepts

### 3.1 EngineRequest
Represents user intent, not implementation details.

- Captures all inputs needed to generate a curve.
- Immutable value object.
- v1 MVP includes:
  - CircularSpiroRequest

Design notes:
- Requests are concrete types.
- Future geometry types introduce new request classes.

---

### 3.2 CurveGenerator (ABC)
Responsible for geometry generation only.

Responsibilities:
- Validate an EngineRequest
- Generate a complete set of points
- Identify meaningful subranges of points (spans)

Explicit non-responsibilities:
- Rendering
- Color decisions
- UI interaction
- Persistence

Each generator:
- Knows exactly one request type
- Produces a GeneratedCurve

---

### 3.3 GeneratorRegistry
A simple, explicit registry mapping request types to generators.

Responsibilities:
- Centralize generator selection
- Eliminate scattered isinstance checks
- Provide clear failure modes when unsupported requests are used

Design constraints:
- Thin wrapper around a dictionary
- Exact type matching in v1
- MRO-based matching may be added later if needed

The orchestrator depends on the registry directly.

---

### 3.4 GeneratedCurve
A pure data container representing the output of a generator.

Contains:
- Ordered list of points (floating-point coordinates)
- Semantic grouping metadata (PointSpans)
- Geometry-related derived values (optional)

Design intent:
- Renderer-agnostic
- Serializable (for future persistence)
- Stable contract between generation and rendering layers

Important:
- GeneratedCurve contains enough information to re-render the curve under the current version of the program.
- Exact cross-version visual equivalence is not guaranteed.

---

### 3.5 PointSpan
Represents a contiguous range of points with semantic meaning.

Examples:
- A single lap around the track
- A single spin of the rolling element

Responsibilities:
- Identify start/end indices
- Declare semantic kind (e.g., LAP, SPIN)
- Provide ordinal ordering

Design constraints:
- Minimal behavior
- No rendering or color logic
- Span-kind branching should be localized (ideally only in planning)

Rationale:
Spans allow rendering decisions (e.g., color changes) to be expressed without embedding presentation logic into the generator.

---

## 4. Rendering Architecture

### 4.1 RenderPlanBuilder
Responsible for mapping GeneratedCurve → RenderPlan.

Responsibilities:
- Interpret spans in the context of rendering settings
- Decide where visual changes occur (e.g., color boundaries)
- Resolve presentation-time decisions that are not geometry-dependent

Non-responsibilities:
- Drawing
- UI
- Geometry generation

This is where v0 color modes are re-expressed declaratively.

---

### 4.2 RenderPlan
A renderer-agnostic description of what should be drawn.

Contains:
- One or more drawable paths
- Per-path style information (pen style, color spec)
- No assumptions about rendering technology

This is the handoff point between domain logic and rendering technology.

---

### 4.3 CurveRenderer (ABC)
Responsible for displaying a RenderPlan.

Responsibilities:
- Translate RenderPlan into concrete drawing operations
- Handle renderer-specific constraints (e.g., integer coordinates)
- Implement animation behavior internally

Non-responsibilities:
- Geometry generation
- Span interpretation
- Randomness decisions

Each renderer:
- Owns its own performance and batching strategies
- Encapsulates renderer-specific utilities privately

Example:
- TurtleGraphicsRenderer

---

## 5. Orchestration

### CurveOrchestrator
Coordinates the pipeline.

Responsibilities:
1. Select generator via GeneratorRegistry
2. Generate curve
3. Build render plan
4. Invoke renderer

Explicit non-responsibilities:
- Persistence
- Random value generation
- UI state management
- Geometry logic

The orchestrator is intentionally thin.

---

## 6. CLI Layer

The CLI is a composition and configuration layer, not a logic layer.

Responsibilities:
- Gather user input
- Maintain transient session state
- Construct EngineRequest and RenderSettings
- Invoke the orchestrator

Design intent:
- CLI should evolve without affecting core logic
- Future GUIs or APIs should reuse the same core pipeline

---

## 7. Randomness Model

Randomness is intentionally split across layers:

- Geometry randomness → CurveGenerator inputs
- Presentation randomness (e.g., color variation) → RenderPlanBuilder

Design principles:
- Randomness must be explicit and inspectable
- Generated inputs can be persisted and replayed
- No hidden randomness inside renderers

---

## 8. Extensibility Roadmap (Architectural Hooks)

The following future features are explicitly supported by the design:

- Non-circular tracks
- Oval or complex rolling elements
- Multiple generators per run
- Persistence via document-oriented storage
- GUI and web-based UIs
- Multiple renderers per run

None of these should require refactoring existing responsibilities.

---

## 9. Guiding Design Principles

- Separation of concerns over minimal class count
- Composition over inheritance
- Practicality over theoretical purity
- Explicit over implicit
- Readability over cleverness
- Architectural clarity over premature optimization

---

## 10. v1 Definition of “Done”

v1 is complete when:

- v0 functionality is fully reproducible
- The CLI is less tedious than v0
- The architecture supports extension without structural changes
- All responsibilities are clearly delineated
- No future feature requires undoing v1 decisions