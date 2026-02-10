# Digital Spirograph

Recreates the nostalgic experience of tracing hypnotic curves with a pen under
the guidance of interlocking plastic gears, but removes the constraints 
imposed by the physical world.

## Basic Concepts
If you have ever used a physical spirograph, the concepts here will be
immediately familiar:

- **Fixed Tracks and Moving Rollers:** Just like the real world, you choose a
  fixed circular "track" and a smaller wheel that rolls along it.
- **The Pen:** You decide where the "pen" sits in that moving wheel.
  Changing this position creates everything from tight loops to wide, sweeping
  waves.
- **Curve Types:**
  - **Hypotrochoid:** Rolling the wheel on the inside of the track
  - **Epitrochoid:** Rolling the wheel on the outside of the track

## Beyond the Plastic Gears

While it feels like the classic kit, this digital version goes significantly
further:

- **Infinite Precision:** No more slipping gears, bumping the track, or ink
  blots. Curves are calculated with mathematical perfection.
- **Automatic Closure:** In the real world, you have to keep spinning until the
  lines meet. This engine uses GCD-based logic to calculate exactly how many
  rotations are needed to perfectly close the loop every time.
- **Full Color Palette:** Choose from millions of color combinations.
- **Random Color Choice:** Choose patterns for random colors, including random
  choice per N laps of the track or N spins of the wheel.
- **Impossible Geometries:**
  - Rolling wheel larger than the circular track.
  - Pen position outside the roller.
- **Discovery:** Use Random, Drift, and Jump modes to let the engine
  explore variations of geometric patterns automatically.

## Getting Started

Installation:
1. Clone the repository to a new directory
2. Create a virtual environment for it with Python 3.12 or higher
3. Run the following from the repository root:
```
pip install .
```

Run the console UI:
```
spirograph
```

Alternatively, you can run the module directly:
```
python3 -m spirograph.main
```

> **Note on the console UI:** The current version is functional but primitive.
> Development has focused primarily on exploring possibilities and on the
> underlying architecture. Improvements to the console UI are on the roadmap.

## Future Roadmap

- **Console UI:** More polished, intuitive, and streamlined experience
- **Persistence:**
  - Save/Restore State Between console UI sessions
  - Save and Replay Drawings
- **Extended Geometries:**
  - Support for non-circular tracks:
    - Bar Track (like in the classic kit)
    - Complex Shape Tracks, based on a "Rounded Rectangle" Concept
  - Support for non-circular rollers:
    - Oval (like the "football" in the classic kit)
    - Lobed (like the "clover" in the classic kit)
  - Support for "Meta-Curves":
    - Changing track position during curve generation:
      - Track position follows a separate curve
      - Track & roller as a roller inside/outside another track
- **Extended Drawing Composition:**
  - Non-centered curves
  - Multiple curves in a single drawing
- **Export:** Export drawings as SVG, GIF, or video files
- **GUIs:** Desktop and Web-based interfaces

## Technical Architecture (For Developers)

Digital Spirograph is built as a modular geometric drawing engine using a
decoupled pipeline architecture.
The design ensures that geometry generation, curve construction, and rendering
remain independent.

### The Pipeline

The engine uses a pluggable sequence: **Request** -> **Generator** ->
**Builder** -> **Renderer**.

- **Request:** Captures user intent and parameters (via the console UI or other
  interfaces).
- **Generator:** Handles pure mathematical calculation of geometric point data
  based on the Request.
- **Builder:** Assembles raw points into a coherent curve structure with
  metadata.
- **Renderer:** Visualizes the constructed curve. The current implementation
  uses Python's Turtle Graphics, but the architecture is designed so that
  future renderers can be plugged in with minimal changes.
