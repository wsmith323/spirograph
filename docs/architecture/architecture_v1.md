# Spirograph v1 Architecture

## Status

This document is the locked ground truth for the v1 refactor. Any changes should be deliberate and explicitly approved to avoid scope drift.
Status: Finalized / Implemented.

## How to use this document

- Treat the responsibilities and boundaries defined here as authoritative.
- Prefer adding new v1 components over refactoring existing v0 code unless explicitly planned.
- When implementation details are unknown, align with these boundaries and keep decisions reversible.

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
- Console-UI-driven interaction
- Turtle-based rendering
- Circular spirograph geometry only (Hypotrochoid and Epitrochoid)
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
  - CircularSpiroRequest (includes `SpiroType`: HYPOTROCHOID or EPITROCHOID)

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
  - Must emit a sequence of `PointSpan` objects covering every complete LAP and SPIN calculated for the curve to close.

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

---

### 3.4 GeneratedCurve
A pure data container representing the output of a generator.

Contains:
- Ordered list of points (floating-point coordinates)
- Semantic grouping metadata (PointSpans)
- Geometry-related derived values (metadata dictionary)

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

---

### 3.6 Color (Value Object)
A renderer-agnostic representation of a color.

Responsibilities:
- Store R, G, B, A components (0-255).
- Provide properties for common formats (e.g., `@property as_rgb` returning `tuple[int, int, int]`).
- Exist in the `rendering` layer as a primitive for `DrawablePath`.

---

## 4. Rendering Architecture

### 4.1 RenderPlanBuilder
Responsible for mapping GeneratedCurve → RenderPlan.

Responsibilities:
- Interpret spans in the context of rendering settings.
- Decide where visual changes occur (e.g., color boundaries).
- Branch logic based on `ColorMode` (Fixed, Random, Per-Lap, Per-Spin, etc.).
  - For "Per" modes, it slices the `GeneratedCurve` into multiple `DrawablePath` segments at `PointSpan` boundaries.
- Resolve presentation-time decisions that are not geometry-dependent.

---

### 4.2 RenderPlan
A renderer-agnostic description of what should be drawn.

Contains:
- One or more drawable paths (each with a `Color` value object and `width`)
- No assumptions about rendering technology

---

### 4.3 CurveRenderer (ABC)
Responsible for displaying a RenderPlan.

Responsibilities:
- Translate RenderPlan into concrete drawing operations.
- Handle renderer-specific constraints (e.g., integer coordinates).
- In Turtle renderer, convert `Color.as_rgb` to the required format.

---

## 5. Orchestration

### CurveOrchestrator
Coordinates the pipeline. It selects the generator, generates the curve, builds the plan, and invokes the renderer.

---

## 6. Console UI Layer

The console UI is a composition and configuration layer, not a logic layer.

Responsibilities:
- Gather user input.
- Maintain transient session state (e.g., `EvolutionState` for drift/jump logic).
- Construct EngineRequest and RenderSettings.
- Provide "Geometry Guidance" and Analysis by interpreting the `EngineRequest` or `GeneratedCurve` metadata (lobes, laps-to-close).
- Invoke the orchestrator.

---

## 7. Randomness Model

Randomness is intentionally split across layers:

- Geometry randomness (resolved into concrete Request values) → Console UI Layer.
- Presentation randomness (resolved into concrete Path colors) → RenderPlanBuilder.

Design principles:
- Randomness must be explicit and inspectable.
- Generated inputs can be persisted and replayed.
- No hidden randomness inside renderers or generators.

---

## 8. Extensibility Roadmap (Architectural Hooks)

The design explicitly supports:
- Non-circular tracks/rollers.
- Persistence via document-oriented storage.
- GUI and web-based UIs.

---

## 9. Guiding Design Principles

- Separation of concerns over minimal class count.
- Composition over inheritance.
- Explicit over implicit.

---

## 10. v1 Definition of “Done”

v1 is complete when:
- v0 functionality is fully reproducible (including all geometry types and color modes).
- The architecture supports extension without structural changes.
- All responsibilities are clearly delineated.
All criteria above are confirmed as met for v1.

---

## Appendix A: Concrete v1 Artifacts (Informational)

### Generation Core
- EngineRequest, CircularSpiroRequest, SpiroType
- CurveGenerator (ABC), GeneratorRegistry
- GeneratedCurve, Point2D, PointSpan (SpanKind: LAP, SPIN)

### Rendering and Presentation
- Color (Value Object)
- RenderSettings, ColorMode
- RenderPlanBuilder, RenderPlan
- CurveRenderer, TurtleGraphicsRenderer

### Orchestration
- CurveOrchestrator
