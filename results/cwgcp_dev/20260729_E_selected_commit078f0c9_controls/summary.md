# FA-PSP 0.3 exploratory pilot (obb_only)

- Scenes: 222
- Random-control eligible scenes: 222
- Relations: 296
- Accepted method candidates: 6
- Selected sources: `{'anchor_rollback': 216, 'proposal_nudge': 6}`
- New-candidate FCL recomputation available: **False**
- Cached FCL available for every selected layout: **False**
- CPU method signal: **True**
- Paper-method upgrade GO: **False**

## Aggregate comparison

| Method | Relation accuracy | Mean mesh pairs | Mean OBB pairs | Mean overlap area | Mean movement |
|---|---:|---:|---:|---:|---:|
| baseline | 0.6115 | 2.22972972972973 | 6.3468 | 1.0738 | 0.0000 |
| floor_prior | 0.6588 | 2.1981981981981984 | 6.2793 | 1.0569 | 0.1073 |
| random | 0.6182 | NA | 6.2568 | 1.0533 | 0.1100 |
| cwgcp | 0.6824 | NA | 6.2703 | 1.0554 | 0.1100 |
| generic | 0.6588 | NA | 6.2523 | 1.0489 | 0.1190 |
| no_nudge | 0.6588 | NA | 6.2793 | 1.0569 | 0.1073 |

## Paired source-cluster bootstrap deltas

| Comparison | Mean | 95% CI |
|---|---:|---:|
| cwgcp_minus_baseline | +0.0709 | [+0.0429, +0.1020] |
| cwgcp_minus_floor_prior | +0.0236 | [+0.0067, +0.0455] |
| cwgcp_minus_random | +0.0642 | [+0.0372, +0.0940] |
| cwgcp_minus_generic | +0.0236 | [+0.0067, +0.0450] |
| cwgcp_minus_no_nudge | +0.0236 | [+0.0067, +0.0447] |

## Mandatory limitations

- This run uses a separately implemented evaluator, but it has not yet been validated on a human-audited subset.
- Archived triples are class-level, so instance-assignment accuracy cannot be claimed without new annotations.
- Cached FCL is available for original/Floor-Prior warm starts. It is only enforced in `cached_fcl` selector mode. Local FCL recomputation for new solver candidates and true room-boundary containment are unavailable and fail closed.
