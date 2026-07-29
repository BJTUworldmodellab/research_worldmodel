# CW-GCP Pilot (cached_fcl)

- Scenes: 531
- Random-control eligible scenes: 531
- Relations: 708
- CW-GCP accepted scenes: 27
- Selected sources: `{'baseline_rollback': 504, 'warm_start': 27}`
- New-candidate FCL recomputation available: **False**
- Cached FCL available for every selected layout: **True**
- CPU solver signal: **False**
- Paper-method upgrade GO: **False**

## Aggregate comparison

| Method | Relation accuracy | Mean mesh pairs | Mean OBB pairs | Mean overlap area | Mean movement |
|---|---:|---:|---:|---:|---:|
| baseline | 0.6285 | 2.096045197740113 | 6.2505 | 1.1115 | 0.0000 |
| floor_prior | 0.6766 | 2.0640301318267418 | 6.1789 | 1.0950 | 0.0957 |
| random | 0.6342 | NA | 6.1714 | 1.0974 | 0.0957 |
| cwgcp | 0.6681 | 2.0828625235404896 | 6.2015 | 1.0957 | 0.0495 |
| generic | 0.6681 | NA | 6.2015 | 1.0957 | 0.0495 |

## Paired scene-bootstrap deltas

| Comparison | Mean | 95% CI |
|---|---:|---:|
| cwgcp_minus_baseline | +0.0395 | [+0.0249, +0.0560] |
| cwgcp_minus_floor_prior | -0.0085 | [-0.0170, -0.0014] |
| cwgcp_minus_random | +0.0339 | [+0.0206, +0.0484] |
| cwgcp_minus_generic | +0.0000 | [+0.0000, +0.0000] |

## Mandatory limitations

- This run uses a separately implemented evaluator, but it has not yet been validated on a human-audited subset.
- Archived triples are class-level, so instance-assignment accuracy cannot be claimed without new annotations.
- Cached FCL is available for original/Floor-Prior warm starts. It is only enforced in `cached_fcl` selector mode. Local FCL recomputation for new solver candidates and true room-boundary containment are unavailable and fail closed.