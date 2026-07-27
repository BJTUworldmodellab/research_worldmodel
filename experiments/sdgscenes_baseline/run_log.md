# SDGScenes Defensive Baseline Run Log

## 2026-07-11

Actions completed:

- Confirmed AutoDL environment is operational.
- Confirmed tmux is installed on cloud.
- Confirmed DeepSeek Claude environment file exists.
- Confirmed cloud `repos/` directory is currently empty, so no project repository has been synchronized yet.
- Ran first-pass GitHub repository audit under AutoDL academic acceleration.
- Created defensive baseline package materials locally for synchronization to cloud archive.

Current conclusion:

- SDGScenes official code/data are not yet available in a no-friction reproducible form.
- SDGScenes should be treated as a strong related system and protocol-analysis reference.
- No direct numeric comparison or outperform claim is allowed.

Next gates:

1. User provides GitHub repository URL or completes GitHub auth on cloud.
2. Copy this package into the project repository under `experiments/sdgscenes_baseline/` or equivalent.
3. If desired, implement the non-official `SDGScenes-inspired strong baseline` using the provided config skeleton.
4. Run bedroom smoke test only after exact split/evaluator paths are known.

