# Related Work to Algorithm Upgrade

## Why the previous repair looked weak in real meshes

The first Relation-Aware InstructScene repair optimized explicit box-level relations too directly. This improved benchmark relation satisfaction, but the rendered 3D-FUTURE meshes exposed a gap between relation correctness and scene plausibility. In particular, living-room prompts often include lamps, side tables, sofas, dining chairs, and coffee tables in the same instruction. A relation such as "sofa right of pendant lamp" can be valid under a box relation metric while still being weak as an interior-design constraint.

The upgraded method therefore treats relation satisfaction as one constraint, not the only objective.

## Papers informing the upgrade

### SDGScenes

SDGScenes frames user-intent indoor scene generation as semantic-dependency-guided constrained optimization. The useful algorithmic lesson for us is not to claim "first relation-aware scene generation", but to add physical and commonsense constraints around relation satisfaction.

Algorithmic impact on our method:

- relation repair remains the target signal;
- collision, boundary, reachability-style validity become verifier signals;
- unsafe repaired scenes should be rejected or down-weighted.

### ATISS

ATISS learns plausible indoor layouts as unordered object sets conditioned on room type and floor plan. The useful lesson is that a valid scene is a structured set, not independent relation pairs.

Algorithmic impact on our method:

- preserve the original generated scene as a layout prior;
- prefer small local moves over large object teleportation;
- avoid destroying furniture groups while satisfying one explicit relation.

### Fast 3D Indoor Scene Synthesis by Learning Spatial Relation Priors

Spatial-relation-prior methods learn recurring object arrangements and use them during synthesis. The useful lesson is that relations should be interpreted through priors over common object neighborhoods.

Algorithmic impact on our method:

- evaluate candidate repairs rather than applying one deterministic displacement;
- choose the candidate with lower movement and lower footprint overlap;
- handle living-room cases conservatively because many relations are weak anchors.

### Structure-Guided Interior Scene Synthesis

Structure-guided synthesis emphasizes support, contact, facing, alignment, and closeness relations. This exposes what our current method does and does not handle.

Algorithmic impact on our method:

- current repair should only claim horizontal spatial relation improvement;
- support/contact/facing are not solved yet;
- vertical height must be preserved unless a true support relation is explicitly modeled.

## Current upgraded method

The new paper-facing variant is `floor_prior`.

It enforces:

```text
allowed:   bounded x/z floor-plane movement
forbidden: y-height changes
preferred: relation-satisfying candidate with low movement and low overlap
fallback: skip repair if no bounded candidate satisfies the relation
```

The direct y-fixed variant is kept only as a diagnostic:

```text
direct y-fixed = relation repair on x/z without scene-prior candidate selection
floor_prior    = relation repair on x/z with bounded movement and overlap-aware selection
```

## Claim-safe storyline

The strongest safe claim is:

> Relation-Aware InstructScene exposes a graph-to-layout grounding gap in instruction-guided 3D indoor scene generation and improves explicit relation realization. A floor-plane, scene-prior-constrained repair variant preserves object heights and reduces implausible large moves, making the method more suitable for real 3D-FUTURE mesh rendering.

Claims to avoid:

- first relation-aware 3D scene generation;
- universally better visual quality;
- implicit commonsense relation understanding;
- superiority over SDGScenes or ReSpace without shared-protocol comparison.
