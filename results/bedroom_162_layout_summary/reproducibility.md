# Reproducibility
**Generated**: 2026-07-18 (updated with 5 new strict one-factor configs)

## Git

- **InstructScene branch**: `param-ablation-layout-repair`
- **InstructScene HEAD**: `70be515`
- **Working tree**: clean
- **Upstream commit**: `a9097a6` (Chenguo Lin, ICLR 2024 spotlight)
- **This results repo branch**: `codex/bedroom-layout-ablation`

## Environment

- **Python**: 3.10.8
- **PyTorch**: 2.1.2+cu118
- **CUDA**: 11.8 (Driver 580.76.05 / CUDA 13.0)
- **GPU**: NVIDIA GeForce RTX 4090 (48 GB VRAM, peak usage ~2.2 GiB)
- **Conda env**: `instructscene_full`
- **OS**: Linux 5.15.0-25-generic
- **Key packages**: shapely, numpy, diffusers, transformers, nltk

## Data Paths

All paths are relative to the InstructScene repository root.

- **Baseline export**: `outputs/official_baseline/bedroom_export_162scene_seed42/` (162 scenes, seed=42)
- **Repair output (new 5 configs)**: `outputs/ablations/strict_one_factor_20260718_seed42/<config_id>/`
- **Repair output (historical 3 configs)**: `outputs/ablations/repair_v0_validation_162scene_seed42_noworse/`
- **Bounds**: `out/bedroom_sgdiffusion_vq_objfeat/bounds.npz`
- **Checkpoints**:
  - `out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth` (fVQ-VAE)
  - `out/bedroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01999.pth` (SG Prior)
  - `out/bedroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth` (SG2SC)
- **HuggingFace cache**: pre-cached in HF_HOME
- **Dataset**: InstructScene preprocessed threed_front_bedroom (162 validation scenes, 21 object types, 10 predicate types)

## Commands

### 1. Baseline Export (162 scenes)

```bash
cd $PROJECT_ROOT
export PYTHONPATH=$(pwd):$PYTHONPATH
export HF_HOME=$HF_CACHE_PATH
python3 src/generate_sg.py \
  configs/bedroom_sg_diffusion_vq_objfeat.yaml \
  --tag bedroom_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae \
  --sg2sc_tag bedroom_sg2scdiffusion_objfeat \
  --checkpoint_epoch 1999 --sg2sc_epoch 1999 --fvqvae_epoch 1999 \
  --n_scenes 162 --seed 42 --output_dir out \
  --export_layout_only \
  --export_output_dir $BASELINE_DIR
```

### 2. Baseline Evaluation (eval-only)

```bash
cd $PROJECT_ROOT
export PYTHONPATH=$(pwd):$PYTHONPATH
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR \
  --output_dir $OUTPUT_DIR/baseline_eval \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz
```

### 3. Repair v0 — Strict One-Factor Ablation (5 new configs)

All configs use the same frozen baseline `$BASELINE_DIR` and seed 42.

```bash
cd $PROJECT_ROOT
export PYTHONPATH=$(pwd):$PYTHONPATH

# Config 1: s0025_d025_i050 (step=0.025, disp=0.25, iter=50)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR \
  --output_dir $OUTPUT_DIR/s0025_d025_i050 \
  --repair --repair_step_size 0.025 --repair_max_displacement 0.25 \
  --repair_max_iter 50 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

# Config 2: s0050_d025_i050 (step=0.050, disp=0.25, iter=50)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR \
  --output_dir $OUTPUT_DIR/s0050_d025_i050 \
  --repair --repair_step_size 0.05 --repair_max_displacement 0.25 \
  --repair_max_iter 50 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

# Config 3: s0075_d015_i050 (step=0.075, disp=0.15, iter=50)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR \
  --output_dir $OUTPUT_DIR/s0075_d015_i050 \
  --repair --repair_step_size 0.075 --repair_max_displacement 0.15 \
  --repair_max_iter 50 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

# Config 4: s0075_d025_i025 (step=0.075, disp=0.25, iter=25)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR \
  --output_dir $OUTPUT_DIR/s0075_d025_i025 \
  --repair --repair_step_size 0.075 --repair_max_displacement 0.25 \
  --repair_max_iter 25 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

# Config 5: s0075_d025_i075 (step=0.075, disp=0.25, iter=75)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR \
  --output_dir $OUTPUT_DIR/s0075_d025_i075 \
  --repair --repair_step_size 0.075 --repair_max_displacement 0.25 \
  --repair_max_iter 75 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz
```

### 4. Historical Configs (pre-existing)

```bash
# Config: s0075_d025_i050 (original central, now dominated)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR --output_dir $OUTPUT_DIR/s0075_d025_i050 \
  --repair --repair_step_size 0.075 --repair_max_displacement 0.25 \
  --repair_max_iter 50 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

# Config: s0075_d035_i050 (aggressive)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR --output_dir $OUTPUT_DIR/s0075_d035_i050 \
  --repair --repair_step_size 0.075 --repair_max_displacement 0.35 \
  --repair_max_iter 50 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

# Config: s0025_d015_i025 (minimal movement, supplementary)
python3 src/ablation_runner.py \
  --input_dir $BASELINE_DIR --output_dir $OUTPUT_DIR/s0025_d015_i025 \
  --repair --repair_step_size 0.025 --repair_max_displacement 0.15 \
  --repair_max_iter 25 --repair_seed 42 \
  --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz
```

## Resource Constraints

- **No downloads**: All models and data pre-cached in HuggingFace cache.
- **No mesh retrieval**: `--export_layout_only` skips `get_textured_objects()`.
- **No rendering**: No Blender calls; visualization disabled.
- **No additional dependencies**: shapely already installed in `instructscene_full`.

## Key Implementation Files

- `src/ablation/evaluators.py` — Overlap, SG-layout consistency, bounds proxy evaluation
- `src/ablation/repairers.py` — Iterative overlap reduction with 3-level SG consistency guard
- `src/ablation/io.py` — Data loading, saving, metrics export
- `src/ablation_runner.py` — Single-config runner (eval-only or repair+eval)
