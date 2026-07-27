# Paper tables for SDGScenes defensive baseline

All percentages are rounded to one decimal place. `pp` means percentage points. Direct numerical comparisons are restricted to methods using the same InstructScene validation split, layout representation, relation thresholds, and evaluator.

## Table 1. Same-protocol relation grounding and mesh-validity results

| Room | Scenes | Relations | Official InstructScene relation acc. | Floor-Prior relation acc. | Floor-Prior gain | Avg. move | Collision-gated relation acc. | Collision-gated gain | Collision-gated mesh-pair rate | Collision-gated mesh-scene rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 162 | 245 | 73.9% | 84.1% | +10.2 pp | 0.78 | 84.5% | +10.6 pp | 6.5% | 51.9% |
| Living room | 192 | 294 | 55.1% | 69.4% | +14.3 pp | 0.88 | 68.7% | +13.6 pp | 3.1% | 83.3% |
| Dining room | 177 | 269 | 59.5% | 72.9% | +13.4 pp | 0.73 | 72.1% | +12.6 pp | 3.3% | 74.6% |
| Overall | 531 | 808 | 62.3% | 75.0% | +12.7 pp | 0.80 | 74.6% | +12.4 pp | 4.2% | 70.8% |

Caption draft: Same-protocol comparison under the official InstructScene validation setup. Floor-Prior refers to `floor_prior_max1.8_mesh_p2_close0.75_far1.6`. The collision-gated variant is used for the mesh-validity claim and falls back to the original layout when repair would worsen mesh collision. Overall relation accuracy is relation-weighted; movement and mesh rates are scene-weighted. The official baseline aggregate mesh-pair and mesh-scene rates are 4.4% and 71.9%, respectively.

## Table 2. Protocol comparability of SOTA and related systems

| Method | Input / protocol | Output representation | Relation supervision / constraints | Same-split comparable? | Runnable locally in this package? | Fair numeric status | Claim role |
|---|---|---|---|---|---|---|---|
| Official InstructScene | Text prompt under existing InstructScene protocol | Object layout with category, translation, size, orientation | Implicit from prompt/protocol; limited original evaluator | Yes | Yes | Direct numerical baseline | Main baseline |
| Ours Floor-Prior | Official InstructScene output + parsed relations | Final repaired object layout | Deterministic verifier/parser or oracle upper bound; floor prior and movement constraints | Yes | Yes | Direct numerical method | Main claim method |
| Ours collision-gated repair | Official InstructScene output + parsed relations | Final repaired object layout | Verifier/parser plus collision gate and movement constraints | Yes | Yes | Direct numerical method for mesh-validity claim | Safety-aware variant |
| SDGScenes official | User intent / semantic dependency graph / VLM constraints | Broader generated or optimized scene layout | Semantic dependency graph, VLM constraints, nonlinear constrained optimization | Not yet verified | No official runnable release located in local audit | Protocol analysis or reported-results context only | Strong related system; no outperform claim |
| SDGScenes-inspired strong baseline | Our relation spec + official InstructScene output | Repaired layout compatible with our evaluator | Explicit graph constraints from our parser/oracle; transparent constrained optimization | Yes, because inputs/evaluator are aligned | Yes | Defensive baseline/control, non-official | Tests whether stronger optimization changes conclusions |
| ReSpace | Text-driven autoregressive scene synthesis/editing | ReSpace/SSR-3DFRONT pipeline output | Model-specific text-driven relation handling and physical plausibility | Not by default | Unknown until official inference succeeds | Feasibility/protocol table unless aligned | Strong SOTA reference; no direct ranking by default |
| RelScene / relation benchmark | Text-driven relation benchmark | Benchmark/evaluation representation | Explicit relation labels/evaluation | Not direct by default | Reference only unless adapted | Relation-evaluation reference | Helps justify metrics, not a direct generator baseline |

Caption draft: Only methods with aligned input split, output representation, object taxonomy, relation thresholds, and evaluator enter the direct numeric table. Methods under different protocols are reported as references or feasibility-bounded controls.

## Table 3. SDGScenes defensive baseline and feasibility-bounded smoke result

| Room | Scenes | Targets | Before all-relation acc. | After all-relation acc. | Gain | Before horizontal acc. | After horizontal acc. | Optimizer edits | Avg. final move / scene | Overlap pairs before→after | OOB centers before→after |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 162 | 243 | 58.8% | 87.7% | +28.8 pp | 54.1% | 87.6% | 72 | 0.92 | 150→142 | 0→0 |
| Living room | 192 | 229 | 33.2% | 76.9% | +43.7 pp | 29.7% | 77.5% | 101 | 0.97 | 412→381 | 0→0 |
| Dining room | 177 | 236 | 33.1% | 72.9% | +39.8 pp | 29.6% | 71.7% | 120 | 0.93 | 332→310 | 0→0 |
| Overall | 531 | 708 | 41.9% | 79.2% | +37.3 pp | 38.0% | 79.0% | 293 | 0.94 | 894→833 | 0→0 |

Caption draft: Same-evaluator SDGScenes-inspired constrained-optimization smoke baseline on H800. This is not an official SDGScenes reproduction. It is a defensive control that uses our relation specification and InstructScene output layouts, then evaluates with the saved relation/geometry checks. Missing object-pair cases were logged separately (`missing_pair_total = 92`) and should be disclosed in the appendix.

