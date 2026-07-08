# Additional Validity Experiments

## Oriented Footprint Collision Proxy

Motivation: the previous geometry sanity check used axis-aligned 2D footprints. That is useful but weak because it can over-count rotated furniture overlap. This additional check computes oriented 2D furniture footprints from saved centers, object sizes, and yaw angles. It is still not full mesh-level collision, but it is a stronger layout-validity proxy than AABB overlap.

| Room | Layout OBB overlap | Repair OBB overlap | Delta | Layout pairs/scene | Repair pairs/scene |
|---|---:|---:|---:|---:|---:|
| bedroom | 0.046569 | 0.041681 | -0.004888 | 0.907 | 0.889 |
| livingroom | 0.054337 | 0.050177 | -0.004160 | 1.911 | 1.833 |
| diningroom | 0.057112 | 0.055276 | -0.001837 | 1.734 | 1.701 |

Interpretation: relation repair does not increase the oriented footprint overlap proxy; it slightly reduces it in all three main-seed room categories. This supports the weaker claim that relation repair does not obviously damage box-level layout validity. It does not support the stronger claim that mesh-level collision is lower, because exact meshes and support/contact surfaces were not evaluated.

Multi-seed summary:

| Room | N | Layout OBB overlap mean | Repair OBB overlap mean | Layout pairs/scene mean | Repair pairs/scene mean |
|---|---:|---:|---:|---:|---:|
| bedroom | 3 | 0.049655 | 0.047408 | 0.963 | 0.938 |
| livingroom | 3 | 0.054220 | 0.051375 | 1.877 | 1.818 |
| diningroom | 3 | 0.057102 | 0.054355 | 1.761 | 1.721 |

## Explicit vs Implicit Relation Audit

Motivation: the current InstructScene relation benchmark was selected for explicit spatial instructions. It should not be used to claim broad implicit commonsense reasoning.

| Room | Explicit scenes | Implicit scenes | Explicit base->repair | Implicit base->repair |
|---|---:|---:|---:|---:|
| bedroom | 162 | 0 | 0.7388->0.8735 | 0.0000->0.0000 |
| livingroom | 192 | 0 | 0.5510->0.7415 | 0.0000->0.0000 |
| diningroom | 177 | 0 | 0.6000->0.7925 | 0.0000->0.0000 |

Interpretation: the existing InstructScene relation benchmark is overwhelmingly explicit spatial language; it is not a valid benchmark for claiming implicit commonsense reasoning. The dining-room explicit relation subset has 265 regex-matched explicit relation instances, while the main selected-relation metric has 269 instances. The paper should report the main selected-relation result for the main benchmark table and use this audit only to delimit claim scope.

## Claim Boundary Outcome

| Proposed claim | Current evidence | Status |
|---|---|---|
| Relation-aware repair improves explicit relation satisfaction on existing InstructScene validation splits. | Main, oracle, pass ablation, distance ablation, and multi-seed runs. | Supported. |
| Visual quality is always better. | Only top-down diagnostic SVGs exist; no rendered image user study or perceptual metric. | Not supported. |
| Mesh-level collision is lower. | AABB and oriented footprint proxies decrease slightly, but exact mesh collision is not measured. | Not supported. |
| The method beats SDGScenes or ReSpace. | No shared-protocol reproduction or published same-split numbers. | Not supported. |
| The method handles all implicit commonsense relations. | Current benchmark contains no implicit-relation scenes under the audit. | Not supported. |
| This is the first relation-aware 3D scene generation method. | Prior work already includes scene graph, semantic dependency, and spatial reasoning methods. | Unsafe; do not claim. |
