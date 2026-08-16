# EG-07 Formal Rerun — Status

Last updated: 2026-08-13 (Phase 1 preflight only — no downloads, no generation)

## 0. Phase

- **Phase 1 preflight** — verifying identity, assets, environment, disk/GPU, commands.
- **NOT** downloading assets. **NOT** starting generation.
- Waiting for user confirmation before Phase 2 (asset acquisition) and Phase 3 (generation).

## 1. Repository identity

| Item | Expected | Observed | Status |
|---|---|---|---|
| EG07 repo HEAD | `3a167d813d74ab18df8762d57ff3b4a47789e3af` | `3a167d813d74ab18df8762d57ff3b4a47789e3af` | ✅ MATCH |
| EG07 branch | — | `codex/eg07-full-export` | ok |
| EG07 working tree | clean | clean (0 changes) | ✅ |
| Frozen config blob SHA-256 | `052ACE5B295348483CE9B6110B5BD7933235424A55CC2108C966431E516829E2` | `052ace5b...829e2` (case-insensitive match) | ✅ MATCH |
| Frozen config path | `configs/eurographics2027/paper_main.yaml` | tracked + `git diff --quiet` clean | ✅ |
| Handoff base | `212b328ab1546aa5760769ccdced32a37c8ed55c` | present (log `212b328`) | ✅ |
| Method code anchor | `feb37414db42faec3d600b66d17186ed3da8a22e` | recorded in manifest/config | ✅ (identity string) |
| InstructScene branch | `param-ablation-layout-repair` (dirty, read-only) | `param-ablation-layout-repair` | ✅ |
| InstructScene HEAD | — | `70be51532d1f0b7d1dad750c34f46fe2bd082985` | ✅ (not modified) |
| InstructScene staged changes | preserve | 7 staged (`.gitignore`, `results/bedroom_162_layout_summary/*`) | ✅ UNTOUCHED |

Config blob command: `git show HEAD:configs/eurographics2027/paper_main.yaml | sha256sum`.

## 2. Checkpoint inventory (InstructScene `out/`)

Present (exact path, bytes, sha256):

| File | Bytes | SHA-256 |
|---|---|---|
| `out/bedroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth` | 411,813,716 | `1ba66bad5b1e158681c0d251bbcdeadd305a0e666a6b71ac764d691dc3a950d0` |
| `out/bedroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01999.pth` | 818,933,394 | `9a69ad6a057face435e537f0fce292ec04e4491334d0a94f20166ee0cdd48217` |
| `out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth` | 365,619,721 | `e1c577fd55681138c7191394db5113cedcb4da5ffab2eac7272d399c33bb9cb4` |
| `out/bedroom_sgdiffusion_vq_objfeat/bounds.npz` | 876 | — |
| `out/threedfront_objfeat_vqvae/objfeat_bounds.pkl` | 159 | — |

Missing (must download from `chenguolin/InstructScene_dataset`; sizes from HF API):

| File | Official bytes |
|---|---|
| `livingroom_sg2scdiffusion_objfeat_epoch_01999.pth` | 411,838,292 |
| `livingroom_sgdiffusion_vq_objfeat_epoch_01459.pth` | 818,979,666 |
| `diningroom_sg2scdiffusion_objfeat_epoch_01999.pth` | 411,838,292 |
| `diningroom_sgdiffusion_vq_objfeat_epoch_01239.pth` | 818,979,666 |

Missing total: **2,461,635,916 bytes ≈ 2.46 GB**.

## 3. Dataset room counts & raw mesh

- Splits CSV test-split (pre-filter) counts: bedroom 248, livingroom 587, diningroom 516.
- Frozen post-filter validation counts: bedroom 162, livingroom 192, diningroom 177 (sum 531).
- `filter_function` present in `src/data/__init__.py` (room filters: bed/living/dining, box count 3–13/21, floor-plan limits, invalid-scene/bbox blacklists).
- **VERIFIED (bounded dataset load via exact generation path `get_dataset_raw_and_encoded`): encoded validation lengths = bedroom 162 / livingroom 192 / diningroom 177 ✅** (matches frozen counts and existing EG-01 anchor JSONs).
- Raw mesh: **0 `raw_model.obj` present** (searched whole InstructScene repo + `/autodl-pub/data`).
- Expected raw mesh: `dataset/3D-FRONT/3D-FUTURE-model/<model_jid>/raw_model.obj` (from `path_to_models` in pickled 3D-FUTURE pkls) — 4232 assets expected; currently ABSENT.
- 3D-FUTURE pickled datasets present: bedroom 2398 / diningroom 2247 / livingroom 2380 objects (unique jids each).

## 4. Python environment (`/root/miniconda3/envs/instructscene_full`, py 3.10.8)

| Module | Status |
|---|---|
| torch 2.1.2+cu118 (CUDA ok, RTX 4090) | ✅ |
| numpy 1.26.4 | ✅ |
| trimesh 4.12.2 | ✅ |
| diffusers 0.26.1 | ✅ |
| transformers 4.38.2 | ✅ |
| huggingface_hub 0.20.3 | ✅ |
| PIL 10.3.0, tqdm | ✅ |
| **fcl (python-fcl)** | ❌ MISSING — `trimesh.collision.CollisionManager` raises `ValueError: No FCL Available!` |
| **pyrender** | ❌ MISSING (visualization only) |
| **cv2** | ❌ MISSING (visualization only) |
| **skimage** | ❌ MISSING (visualization only) |
| **accelerate** | ❌ MISSING |

⚠️ **BLOCKER — `fcl` (python-fcl) is required for `mesh_collision=true`.** Without it, `mesh_collision_quality()` catches the exception and returns `available: False` for every scene, silently degenerating the frozen collision gate to "always repair". Must `pip install python-fcl` (or equivalent) before formal generation.
- `nltk` cmudict corpus present at `cache/nltk_data/`; requires `NLTK_DATA=<root>/cache/nltk_data` at runtime.

## 5. Disk & GPU

- GPU: RTX 4090, 49140 MiB total, ~48510 MiB free (48 GB free VRAM) ✅.
- CPU: 20 cores; RAM: ~1007 GB total, ~918 GB available.
- `/root/autodl-tmp` (`/dev/md0`): 50 GB total, **30.87 GB free**.
- `/` overlay: 22.83 GB free.
- `/dev/shm` tmpfs: 45 GB (RAM).
- `/autodl-pub/data` (AutoFS): 5.7 TB free but **READ-ONLY**, no InstructScene/3D-FRONT copy present.

## 6. Missing-asset acquisition plan (disk-safe; NOT executed this phase)

Source: HuggingFace dataset `chenguolin/InstructScene_dataset` (public, no key).

1. **Checkpoints (2.46 GB)** — `huggingface_hub.hf_hub_download` → hardlink/copy into isolated `out/`. Leaves ~28.4 GB free.
2. **3D-FRONT.zip (26.4 GB)** — stream-extract via `curl -L <hf url> | bsdtar -xvf - -C <dest>` (install `libarchive-tools`); never retain the ZIP. Peak = extracted size only.

Disk math:
- Free now: 30.87 GB.
- After 2.46 GB checkpoints: ~28.41 GB.
- 3D-FRONT extracted size unknown (ZIP 26.4 GB; meshes ≈ 26–32 GB) → **does NOT safely fit** alongside checkpoints on `/root/autodl-tmp`.
- Fallback: extract 3D-FRONT to `/dev/shm` (45 GB RAM) then selectively keep only `raw_model.obj` on `/root/autodl-tmp`; or free the 4.63 GB `InstructScene.zip` cache duplicate; or mount/use a data disk. Repo's own `stream_extract_3d_front.sh` gates risky extraction behind `ALLOW_RISKY_3DFRONT_EXTRACT=1`.

## 7. Frozen generation commands (three rooms)

Entrypoint: `results/relation_aware_generate_sg.py` (EG07 repo; imports InstructScene `src.*`).
Run with cwd = InstructScene repo, `NLTK_DATA=<root>/cache/nltk_data`, `PYTHONPATH` = EG07 repo.

Per room `R` in {bedroom,livingroom,diningroom} with VQ epoch `E` (1999/1459/1239):

```
python results/relation_aware_generate_sg.py configs/${R}_sg_diffusion_vq_objfeat.yaml \
  --tag ${R}_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae --fvqvae_epoch 1999 \
  --sg2sc_tag ${R}_sg2scdiffusion_objfeat --sg2sc_epoch 1999 \
  --checkpoint_epoch ${E} \
  --n_scenes 0 --n_workers 0 --device 0 --seed 0 \
  --relation_source parsed \
  --repair_strategy floor_prior --repair_passes 2 \
  --max_repair_move 1.8 --repair_overlap_weight 1.0 \
  --close_distance 0.75 --far_distance 1.6 \
  --mesh_collision \
  --output_suffix floor_prior_max1.8_mesh_p2_close0.75_far1.6 \
  --output_dir <ISOLATED_OUT>
```

Isolated output strategy (preserves dirty InstructScene tree + old outputs):
- Create `eg07_formal_20260813/instructscene_out/`.
- For each tag, make a fresh dir `instructscene_out/<tag>/`, symlink only `checkpoints/` and `bounds.npz` (and fVQ-VAE `objfeat_bounds.pkl`) from InstructScene `out/<tag>/`; let `generated_scenes/` be created fresh there.
- Result JSONs land in `instructscene_out/<tag>/generated_scenes/epoch_XXXXX/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json`.
- This never writes into `code/InstructScene`.

## 8. Downstream (after generation, Phase 3+)

1. `scripts/export_eg07_layouts.py` (3 inputs → `results/eg07/formal_candidate/layouts.json`, `--artifact-status formal_candidate`, `--profile full`).
2. `scripts/validate_eg07_layouts.py --profile full` (expect 531 scenes / 1062 layouts).
3. `evaluation/independent_relation_evaluator.py` (EG-05).
4. `scripts/run_eg06_movement_baselines.py --seeds 0,1,2` (EG-06).

## 9. Blocker summary

- **PRECHECK_BLOCKED** (for formal generation). Blockers:
  1. `fcl` (python-fcl) missing → collision gate cannot produce real FCL pairs.
  2. 4 living/dining checkpoints missing (2.46 GB) — download required.
  3. Raw 3D-FRONT mesh (26.4 GB) missing + insufficient disk to hold ZIP+extracted on `/root/autodl-tmp`.

## 10. Phase 2 (assets + smoke) — progress

### 10.1 FCL
- `pip install python-fcl` → `python-fcl 0.7.0.11` (+ Cython 3.2.9).
- `import fcl` → `FCL_OK 0.7.0.11`.
- `trimesh.collision.CollisionManager()` now works (`in_collision_internal` returns `(True, {('a','b')})`).
- Versions: torch 2.1.2+cu118, numpy 1.26.4, trimesh 4.12.2, fcl 0.7.0.11, pyrender MISSING (viz-only, not required for mesh-collision smoke).

### 10.2 Checkpoints
4 living/dining checkpoints downloaded (hf_hub_download, resume-safe) and VERIFIED (size + SHA-256 all match):
| file | size | sha256 | status |
|---|---|---|---|
| livingroom_sg2scdiffusion_objfeat_epoch_01999.pth | 411838292 | 5746fe10…12da | OK |
| livingroom_sgdiffusion_vq_objfeat_epoch_01459.pth | 818979666 | f4d4554b…e819 | OK |
| diningroom_sg2scdiffusion_objfeat_epoch_01999.pth | 411838292 | b7f84a69…1529 | OK |
| diningroom_sgdiffusion_vq_objfeat_epoch_01239.pth | 818979666 | faa7e87c…897d | OK |

Existing (unchanged): bedroom SG2SC 411813716/1ba66bad…, bedroom VQ 818933394/9a69ad6a…, fVQ-VAE 365619721/e1c577fd…, objfeat_bounds.pkl 159 B.

### 10.3 Runtime (isolated)
- `eg07_formal_20260813/runtime/` with symlinked src/configs/dataset + per-tag checkpoint symlinks; fresh `out/<tag>/generated_scenes/` (not created yet).
- Config blob SHA re-confirmed: `052ace5b…829e2`.

### 10.4 3D-FRONT mesh
- ZIP: 157003 entries, top-level `3D-FRONT/`, `3D-FUTURE-model/<jid>/{raw_model.obj,texture.png,bbox_vertices.npy}`.
- Full obj+texture+bbox uncompressed = 36.66 GB; but only 4232 model jids (union of 3 room pkls) are needed → selective ≈ 9 GB.
- Download: hf-mirror.com (fast in CN) via aria2c 16-conn, resilient loop re-resolving signed URL. Expected sha256 `97a3bcaa…7d15`. In progress.

## 12. Unattended handoff (2026-08-13 17:14:42)

- Mode: unattended, resume-safe, tmux.
- **Download process**: PID 9574 (resilient loop, PPID=1 detached) + aria2c PID 9589. Progress: `19GiB/24GiB(77%)`.
- **tmux session**: `eg07-assets` running `phase2_continue.sh` (PID 13478).
- **Logs**: download → `download_3dfront.log`; post-download+smoke → `phase2.log`; smoke per-room → `smoke_{room}.log`.
- **Resume command**: `tmux attach -t eg07-assets`
- **Monitor command**: `tail -f /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase2.log` and `tail -f /root/autodl-tmp/relation_grounding/eg07_formal_20260813/download_3dfront.log`
- **Post-download pipeline (automatic)**: verify sha256 (97a3bcaa…) → selective-extract 4232 jids → verify raw_model.obj count → trimesh spot-check → delete verified ZIP → symlink mesh into runtime → run bedroom/livingroom/diningroom 1-scene smoke → verify per_scene=1 + mesh available=true → update status.md → STOP (no 531-scene run).
- **Safety**: aborts with ASSET_BLOCKED if /dev/shm < 5 GiB, sha256 mismatch, or obj count < 4000.

## 14. Auto-shutdown armed (2026-08-13 17:21:43)

- **Shutdown watcher**: tmux session `eg07-shutdown` running `shutdown_finalize.sh` (PID 13794). Detached (survives SSH exit).
- **Pipeline tmux**: `eg07-assets` running `phase2_continue.sh` (PID 13478).
- **Download progress at arm time**: `19GiB/24GiB(80%)`.
- **Trigger condition**: when `phase2.log` contains `PHASE2 CONTINUE DONE` or `ASSET_BLOCKED`.
- **On PASS**: move mesh `/dev/shm/eg07_3d_front_20260813/3D-FRONT` → `/root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT` (disk-check first), re-verify raw_model.obj count + trimesh, repoint `runtime/dataset/3D-FRONT` symlink, remove /dev/shm copy.
- **On BLOCKED**: keep status.md/logs (already persistent); move aria2 partial + .aria2 to eg07_assets/ if space allows.
- **Final**: sync → `/usr/bin/shutdown -h now`.
- **Log**: `shutdown_finalize.log`.

## 13. AUTO-SHUTDOWN FINAL STATE (2026-08-13 17:26:38)
- final_status: BLOCKED
- reason: phase2 reported ASSET_BLOCKED
- persistent mesh: /root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT (0 raw_model.obj)
- smoke JSONs/logs/status.md on /root/autodl-tmp: yes
- shutdown_finalize log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/shutdown_finalize.log

## 15. Phase 2 resume (3D-FRONT.zip only) — 2026-08-13 19:34:15
- state: DOWNLOAD_VERIFIED
- path: /root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT.zip
- size: 26400916556
- sha256: 97a3bcaa1cba416f20f5e5aee969b0cffc31e1588b9b780391d318d0e0b97d15
- aria2c exit code: 0
- download log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/download_3dfront.log
- resume log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/resume_3dfront.log

## 19. Phase 2b ARMED (2026-08-14 09:36:19)

- **mode**: unattended, detached tmux, resume-safe.
- **tmux sessions**:
  - `eg07-smoke` — pipeline `phase2b_smoke.sh` (PID 3012)
  - `eg07-watch` — auto-shutdown watcher `shutdown_watcher_20260814.sh` (PID 3005)
- **manifest**: `/root/autodl-tmp/relation_grounding/eg07_formal_20260813/manifest_model_jids_20260814.txt`
  - lines = 4232 (exactly), sha256 = `c95df2cdd9c16de445539aa9a641d2598da67607e01e1588a34be0c17021269d`
  - rooms sidecar: `manifest_rooms_20260814.json` (bedroom 2398 / livingroom 2380 / diningroom 2247)
- **main log**: `/root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase2b.log`
- **watcher log**: `/root/autodl-tmp/relation_grounding/eg07_formal_20260813/shutdown_watcher_20260814.log`
- **status file**: `/root/autodl-tmp/relation_grounding/eg07_formal_20260813/status.md`
- **ZIP** (pre-delete): `/root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT.zip` size=26400916556 sha256=97a3bcaa…7d15 (re-verified in step 1)
- **selective dest**: `/dev/shm/eg07_3d_front_20260814/3D-FRONT` (full per-jid dirs, ~50882 files ≈10 GB)
- **persist dest**: `/root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT`
- **runtime symlink** (step 7): `runtime/dataset/3D-FRONT` → persistent mesh
- **smoke** (step 8, 1 scene each): bedroom epoch 1999 / livingroom 1459 / diningroom 1239; SG2SC 1999; fVQ-VAE 1999; seed=0, n_scenes=1, n_workers=0, device=0, mesh_collision=true, suffix `eg07_smoke_floor_prior_max1.8_mesh_p2_close0.75_far1.6_20260814`
- **env**: python `/root/miniconda3/envs/instructscene_full` (torch 2.1.2+cu118, trimesh 4.12.2, fcl 0.7.0.11), NLTK_DATA=…/cache/nltk_data
- **terminal markers**: `ASSET_SMOKE_PASS` (all 3 smokes verified) or `ASSET_BLOCKED` (any failure) → watcher then `sync` + `shutdown -h now`
- **scope**: STRICTLY Phase 2b only — no 531-scene formal run. InstructScene repo NOT modified/reset/cleaned (read-only; runtime uses symlinked src/configs/dataset).

## 17. Phase 2b COMPLETE — ASSET_SMOKE_PASS (2026-08-14 09:39:24)
- manifest: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/manifest_model_jids_20260814.txt (lines=4232, sha256=c95df2cdd9c16de445539aa9a641d2598da67607e01e1588a34be0c17021269d)
- selective assets: /root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT (raw_model.obj=4232, sample_digest=0ed49c47b32e07cd29fe3695f2bd1790925ba3336884e54d67e2262516fc074a)
- ZIP deleted: /root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT.zip (was 26400916556 bytes, sha256 97a3bcaa1cba416f20f5e5aee969b0cffc31e1588b9b780391d318d0e0b97d15 verified)
- runtime symlink: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/runtime/dataset/3D-FRONT -> /root/autodl-tmp/relation_grounding/eg07_assets/3D-FRONT
- smoke: bedroom(1999)/livingroom(1459)/diningroom(1239), n_scenes=1, seed=0, mesh_collision=true
- smoke logs: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/smoke_bedroom_20260814.log, /root/autodl-tmp/relation_grounding/eg07_formal_20260813/smoke_livingroom_20260814.log, /root/autodl-tmp/relation_grounding/eg07_formal_20260813/smoke_diningroom_20260814.log
- verify: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/verify_shm_20260814.log, /root/autodl-tmp/relation_grounding/eg07_formal_20260813/verify_persist_20260814.log
- main log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase2b.log
- /dev/shm free: 45.0 GiB, /root/autodl-tmp free: 19.1 GiB

## 18. Auto-shutdown watcher final (2026-08-14 09:39:49)
- watcher_status: ASSET_SMOKE_PASS
- main log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase2b.log


## 20. Phase 3 FORMAL RUN STARTED (2026-08-14 09:55:24)

- **status**: FORMAL_RUN_STARTED (531-scene frozen rerun, sequential)
- **tmux session**: `eg07-formal` (single session; no auto-shutdown watcher deployed)
- **PID**: main script `phase3_formal.sh` = 2345; current generation `python relation_aware_generate_sg.py` = 2396 (bedroom)
- **preflight**: PASS — git HEAD `3a167d813d74ab18df8762d57ff3b4a47789e3af`, config blob SHA `052ace5b…829e2`, clean tree, 4232 raw_model.obj, 7/7 checkpoint symlinks resolved, disk 20 GiB free, GPU 48510 MiB free, no residual/duplicate processes.

### Targets (frozen fair-comparison order, run sequentially — no parallel GPU)
| room | vq_epoch | target scenes |
|---|---|---|
| bedroom | 1999 | 162 |
| livingroom | 1459 | 192 |
| diningroom | 1239 | 177 |
| **total** | | **531** |

### Frozen parameters (identical to passing smoke; only n_scenes 1→0)
seed=0, relation_source=parsed, repair_strategy=floor_prior, repair_passes=2, max_repair_move=1.8, repair_overlap_weight=1.0, close_distance=0.75, far_distance=1.6, mesh_collision=true, sg2sc_epoch=1999, fvqvae_epoch=1999, output_suffix=floor_prior_max1.8_mesh_p2_close0.75_far1.6. No rendering, no mesh copying.

### Output paths
- source result JSONs: `runtime/out/<tag>/generated_scenes/epoch_<E>/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json`
- formal export: `results/eg07/formal_candidate/layouts.json` + `validation.json` + `validation_recheck.json`

### Logs
- main: `phase3.log`
- per-room generation: `formal_bedroom_20260814.log`, `formal_livingroom_20260814.log`, `formal_diningroom_20260814.log`
- per-room verification: `verify_formal_bedroom_20260814.log`, `verify_formal_livingroom_20260814.log`, `verify_formal_diningroom_20260814.log`
- GO/NO-GO summary: `phase3_gonogo_20260814.txt`

### Estimated duration
~1–2 hours, dominated by per-scene FCL mesh-collision (O(objects²)).

### Monitor
`tmux attach -t eg07-formal` · `tail -f /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase3.log`

## Phase 3 room DONE — bedroom (2026-08-14 09:59:37)
- target: 162, epoch: 1999, output_suffix: floor_prior_max1.8_mesh_p2_close0.75_far1.6
- generation log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/formal_bedroom_20260814.log
- verification log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/verify_formal_bedroom_20260814.log
- result JSON: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/runtime/out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json

## Phase 3 room DONE — livingroom (2026-08-14 10:11:16)
- target: 192, epoch: 1459, output_suffix: floor_prior_max1.8_mesh_p2_close0.75_far1.6
- generation log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/formal_livingroom_20260814.log
- verification log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/verify_formal_livingroom_20260814.log
- result JSON: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/runtime/out/livingroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01459/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json

## Phase 3 room DONE — diningroom (2026-08-14 10:20:41)
- target: 177, epoch: 1239, output_suffix: floor_prior_max1.8_mesh_p2_close0.75_far1.6
- generation log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/formal_diningroom_20260814.log
- verification log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/verify_formal_diningroom_20260814.log
- result JSON: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/runtime/out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01239/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json

## Phase 3 BLOCKED (2026-08-14 10:20:41)
- reason: export_eg07_layouts.py failed
- main log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase3.log
- status: FORMAL_BLOCKED

## Phase 3 EXPORT-ONLY RESUME (2026-08-14 10:29:52)
- supersedes the 10:20:41 FORMAL_BLOCKED (exporter detect_room bug); audit record retained above
- generation commit: 3a167d813d74ab18df8762d57ff3b4a47789e3af (unchanged; no generation re-run)
- exporter fix commit: e5fe83731bae789350574312847db5eaeacb8259
- frozen config SHA: 052ace5b295348483ce9b6110b5bd7933235424a55cc2108c966431e516829e2 (unchanged)
- input JSON SHA-256:
  - bedroom:    b1a59c825c7cdc0cd992c2516107b38a750131c45fa51b345b5216e48f6da3d5 (per_scene=162)
  - livingroom: 464df22e65b219192e8704175a86a540ec4000629d958e0be1977be762cdd995 (per_scene=192)
  - diningroom: 7db924be530bb823e621d28fedc00fcb5524c3cb773be1215f50262ef78ddd3f (per_scene=177)
- exported layouts: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/results/eg07/formal_candidate/layouts.json
- export validation: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/results/eg07/formal_candidate/validation.json
- independent recheck: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/results/eg07/formal_candidate/validation_recheck.json
- GO/NO-GO summary: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase3_gonogo_20260814.txt
- resume log: /root/autodl-tmp/relation_grounding/eg07_formal_20260813/phase3_export_resume_20260814.log


## Phase 3 formal summary (2026-08-14)

### Room-level metrics (frozen fair-comparison order)

| room | target | per_scene | mesh_eval | base_rel_acc | repair_rel_acc | avg_move | base_mesh_pair | repair_mesh_pair | mesh_avail | ident_stable | no_fallback |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bedroom | 162 | 162 | 162 | 0.7429 | 0.8531 | 0.8404 | 0.0708 | 0.0753 | True | True | True |
| livingroom | 192 | 192 | 192 | 0.5680 | 0.6973 | 1.0078 | 0.0306 | 0.0321 | True | True | True |
| diningroom | 177 | 177 | 177 | 0.6097 | 0.7435 | 0.8522 | 0.0323 | 0.0328 | True | True | True |

### Total
- scenes: 531 / 531
- layouts: 1062 / 1062
- target_relations: 808
- relation_export_status: {'direct': 678, 'protocol_mapped_composite': 130}
- gate_decision_by_room: {'bedroom': {'fallback_baseline': 8, 'repair': 154}, 'diningroom': {'fallback_baseline': 13, 'repair': 164}, 'livingroom': {'fallback_baseline': 18, 'repair': 174}}

### GO / NO-GO (frozen structural contract)

| check | result | GO/NO-GO |
|---|---|---|
| bedroom: per_scene == 162 | PASS | GO |
| bedroom: mesh evidence available (all scenes) | PASS | GO |
| bedroom: object identity stable (all scenes) | PASS | GO |
| bedroom: no silent fallback (mesh_eval == 162) | PASS | GO |
| livingroom: per_scene == 192 | PASS | GO |
| livingroom: mesh evidence available (all scenes) | PASS | GO |
| livingroom: object identity stable (all scenes) | PASS | GO |
| livingroom: no silent fallback (mesh_eval == 192) | PASS | GO |
| diningroom: per_scene == 177 | PASS | GO |
| diningroom: mesh evidence available (all scenes) | PASS | GO |
| diningroom: object identity stable (all scenes) | PASS | GO |
| diningroom: no silent fallback (mesh_eval == 177) | PASS | GO |
| total scenes == 531 | PASS | GO |
| total layouts == 1062 | PASS | GO |
| independent validator status == PASS | PASS | GO |
| provenance complete (formal_candidate, commit, config SHA, git-clean) | PASS | GO |
| bedroom: gate decisions sum == 162 (repair+fallback) | PASS | GO |
| livingroom: gate decisions sum == 192 (repair+fallback) | PASS | GO |
| diningroom: gate decisions sum == 177 (repair+fallback) | PASS | GO |
| gate counts reconciled (no scene skipped in gate) | PASS | GO |

### VERDICT: GO

## 21. EG-07 Final Evaluation COMPLETE — EG07_FINAL_PASS (2026-08-14 10:35)

Runbook Step 4–6. No generation/smoke/unzip/export re-run.

### Input identity
- layouts.json: results/eg07/formal_candidate/layouts.json
- size: 5952882 bytes
- SHA-256: 663ce5ff76698358c47e9542563bd01a788bc90efb9f299e7c261da2399e281d
- validation.json: PASS, errors [], warnings []
- validation_recheck.json: PASS, errors [], warnings []

### EG-05 (independent relation evaluator)
- output: results/independent_eval/eg2027/eg07_full_independent_eval/
- audit: n_layouts=1062, per_relation=1616, per_scene=1062, missing_baseline_scenes=[], input SHA matches, protocol eg2027-eg05-v1, imports_repair_or_optimizer_modules=false
- relation accuracy (baseline -> main): overall 0.6349 -> 0.6399 (+0.0050; 513 -> 517 satisfied)
  - bedroom 0.7265 -> 0.7306 (+0.0041)
  - livingroom 0.6054 -> 0.6122 (+0.0068)
  - diningroom 0.5836 -> 0.5874 (+0.0037)
- missing target objects (per variant, in denominator): overall 93 (bedroom 17 / livingroom 40 / diningroom 36); unsupported: 0 (explicitly counted, none present)

### EG-06 (movement-matched baselines, seeds 0,1,2)
- output: results/independent_eval/eg2027/eg06_full_movement_baselines/
- audit: run_scope=full, input_artifact_status=formal_candidate, input_scene_count=531, seeds=[0,1,2], input SHA == EG-05 SHA, no scene/variant skipped (2655 movement rows = 531x5)
- overall relation accuracy:
  - baseline 0.6349 | main 0.6399 | random seed0 0.6225 / seed1 0.6250 / seed2 0.6287 (mean 0.6254) | generic_relation_optimizer 0.6411
  - main vs baseline +0.0050; main vs random-mean +0.0144; main vs generic -0.0012
- fairness: random exact XZ movement-matched; generic within budget

### Gate / mesh
- gate repair 492 / fallback_baseline 39; mesh_available 531/531
- baseline collision pairs total 1075; chosen main 1061 (<= baseline, safety non-worsening)

### GO/NO-GO VERDICT: GO
- all structural gates GO; scientific metric gates REPORTED (significance -> EG-08); mesh safety GO; unsupported/missing explicitly counted GO.
- full tables: eg07_gonogo_20260814.md (+ .csv/.json); metrics: eg07_final_metrics_20260814.json (+ .csv); report: eg07_final_report_20260814.md
