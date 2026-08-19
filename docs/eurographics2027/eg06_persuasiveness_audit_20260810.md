# EG-06 Persuasiveness Audit

Date: 2026-08-10
Task: Check whether EG-06 results are persuasive enough for paper claims
Branch: `agent/eg01-eg02-eurographics2027`

## Short Verdict

Current EG-06 is **methodologically useful but not yet persuasive as paper
evidence**.

It is persuasive for this limited claim:

> The EG-06 runner can generate exact movement-matched random baselines, a
> budget-matched generic optimizer baseline, and evaluate them through the
> EG-05 independent evaluator.

It is **not** persuasive for this paper claim yet:

> Collision-gated Floor-Prior outperforms fair movement-matched baselines on the
> full InstructScene validation set.

That stronger claim still requires EG-07 full normalized layout export and EG-08
paired confidence intervals.

## What Was Checked

Command:

```powershell
& "C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/check_eg06_baseline_fairness.py
```

Result:

```text
EG-06 fixture fairness check passed.
random_baselines=exact per-object XZ movement matched
generic_optimizer=budget matched, may use less movement
claim_readiness=fixture only; full EG-07 export still required
```

Additional checks:

```text
py_compile: PASS
EG-05 evaluator unit tests: PASS, 4 tests
EG-06 runner execution: PASS
```

## Strengths

| Point | Assessment |
|---|---|
| Random baseline fairness | Strong for fixture. Random seeds move the same objects by the same XZ distance as the main method. |
| Independent evaluator integration | Good. Outputs are evaluated by `evaluation/independent_relation_evaluator.py`. |
| Reproducibility | Good. Fixture input, augmented layouts, summary, movement audit, and audit JSON are committed. |
| Seed coverage | Minimal acceptable starting point. Seeds 0, 1, 2 are present. |
| Claim boundary | Clear. Report and audit mark the result as fixture-only. |

## Weaknesses

| Issue | Why it matters | Severity |
|---|---|---|
| Fixture only has 3 scenes and 3 relations | Too small and too easy; cannot estimate real effect size. | Major |
| Generic optimizer matches main result on fixture | This is a useful sanity check, but not evidence that the main method is better than a generic optimizer. | Major |
| No mesh collision in fixture | EG04 main method claim includes mesh-collision non-worsening, but EG06 fixture is center/box-only. | Major |
| No paired CI | EG06 cannot support statistical superiority until EG08. | Major |
| Full layout export missing | Runner cannot operate on 531 scenes until EG07 exports normalized layouts. | Blocking |

## Code Audit Finding

The first EG06 runner version allowed the generic optimizer to choose relation
pairs from the currently mutated layout. That could violate the EG-05 principle
that instance pairs are frozen from the baseline layout.

Fix:

- `scripts/run_eg06_movement_baselines.py` now precomputes frozen baseline
  pairs per scene and reuses them during generic optimization.

This fix matters for full runs with repeated object instances and multiple
relations.

## Paper-Use Recommendation

Do not put the current EG06 fixture table into the main paper as evidence.

Safe wording for internal notes:

> EG-06 baseline infrastructure is implemented and passes fixture-level
> fairness checks. Full fair-baseline evidence remains pending the EG-07
> normalized layout export and EG-08 paired confidence intervals.

Unsafe wording:

> The method outperforms movement-matched random and generic optimizer
> baselines.

## Minimum Evidence Needed Before EG06 Is Convincing

1. EG07 exports paired `baseline` and `collision_gated_floor_prior` layouts for
   all 531 InstructScene validation scenes.
2. EG06 runner generates:
   - baseline;
   - collision-gated Floor-Prior;
   - random movement-matched seeds 0, 1, 2;
   - generic budget-matched optimizer.
3. EG05 evaluator produces per-scene CSV for every variant.
4. EG08 computes paired bootstrap confidence intervals.
5. Main method vs random-seed mean has 95% CI lower bound above 0.
6. Safety metrics do not worsen relative to baseline.
