# Digital Spirograph

## Project Overview

Digital Spirograph is a modular geometric drawing engine that produces
high-precision spirograph curves through a decoupled pipeline architecture.
The design keeps geometry generation, curve construction, and rendering
independent so each stage can evolve without entangling the others.

## Core Features

- Dual Geometry: Hypotrochoids and Epitrochoids.
- Automatic Closure: GCD-based period sampling for perfectly closed curves.
- Advanced Presentation: High-fidelity RGBA color model with span-aware modes
  (per lap/spin).
- Evolutionary Discovery: Drift and Jump modes for parameter exploration.

## Getting Started

Run the application CLI with:

```
python3 -m spirograph.main
```

## Architecture & Extensibility

The engine uses a pluggable pipeline: Request -> Generator -> Builder ->
Renderer. This keeps request handling, curve generation, and rendering
independent while making it straightforward to add new request types,
builders, or renderers. The currently available renderer implementation uses 
Python Turtle Graphics.

## Future Roadmap

- Support for non-circular tracks and rollers.
- Multiple layered curves in a single drawing.
- Saving and replaying curve configurations.
- SVG, GIF, and video export.
- Additional UIs:
  - CLI with between-execution state save/restore
  - Desktop GUI
  - Rich Web App
