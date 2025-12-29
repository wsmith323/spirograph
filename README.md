# Digital Spirograph

Digital Spirograph is a modular, high-precision geometry tool for generating
and rendering spirograph curves with rich visual variation and guided control.

## Features

- Dual Geometry: Hypotrochoids and Epitrochoids.
- Advanced Color Modes: Fixed, Random, Per-Lap, and Per-Spin variations.
- Evolutionary Randomness: Drift and Jump modes for continuous discovery.
- User Controls: Parameter locking and mathematical guidance.

## Getting Started

Run the application with:

```
python3 -m spirograph.main
```

## Extensibility

The pipeline architecture is intentionally pluggable. New `EngineRequest` types
can introduce additional geometry, new `CurveGenerator` implementations can
produce those curves, and new `CurveRenderer` backends can target different
output systems without changing core logic.

## Future Roadmap

- Persistence: Save and replay curve configurations via document-oriented
  storage.
- Advanced Geometry: Support for non-circular tracks and complex rolling
  elements.
- Rich Output: Export functionality for SVG, high-resolution raster images, and
  animated GIFs.
- Multiple Curves: Support for layering multiple geometric requests in a single
  render plan.
- Web/GUI Interfaces: Transitioning beyond the CLI while reusing the core
  generation pipeline.
