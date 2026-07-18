# Reproducibility
**Generated**: 2026-07-08

## Git
- **Branch**: param-ablation-layout-repair
- **HEAD**: 70be515
- **Working tree**: clean
- **Repository**: /path/to/InstructScene
- **Upstream commit**: a9097a6 (Chenguo Lin, ICLR 2024 spotlight)

## Environment
- **Python**: 3.10.8
- **PyTorch**: 2.1.2+cu118
- **CUDA**: 11.8 (Driver 580.76.05 / CUDA 13.0)
- **GPU**: NVIDIA GeForce RTX 4090 (48 GB VRAM, peak usage ~2.2 GiB)
- **Conda env**: instructscene_full
- **OS**: Linux 5.15.0-25-generic
- **Key packages**: shapely, numpy, diffusers, transformers, nltk

## Data Paths
- **Baseline export**: `outputs/official_baseline/bedroom_export_162scene_seed42/` (162 scenes, seed=42)
- **Repair output**: `outputs/ablations/repair_v0_validation_162scene_seed42_noworse/`
- **Summary**: `outputs/ablations/final_bedroom_162_summary/`
- **Checkpoints**:
  - `out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth` (fVQ-VAE)
  - `out/bedroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01999.pth` (SG Prior)
  - `out/bedroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth` (SG2SC)
- **HuggingFace cache**: `/path/to/huggingface-cache/`
- **Dataset**: InstructScene preprocessed threed_front_bedroom (162 validation scenes, 21 object types, 10 predicate types)

## Commands

### 1. Baseline Export (162 scenes)
```bash
cd /path/to/InstructScene
export PYTHONPATH=$(pwd):$PYTHONPATH
export HF_HOME=/path/to/huggingface-cache
python3 src/generate_sg.py \
  configs/bedroom_sg_diffusion_vq_objfeat.yaml \
  --tag bedroom_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae \
  --sg2sc_tag bedroom_sg2scdiffusion_objfeat \
  --checkpoint_epoch 1999 --sg2sc_epoch 1999 --fvqvae_epoch 1999 \
  --n_scenes 162 --seed 42 --output_dir out \
  --export_layout_only \
  --export_output_dir .../bedroom_export_162scene_seed42
```

### 2. Repair v0 (4 configs)
```bash
# Run the pilot script (see run_args.json for exact parameters)
# Configs: baseline, s0075_d035_i050, s0075_d025_i050, s0025_d015_i025
python3 .../repair_pilot_162.py  # inline script; parameters in run_args.json
```

## Resource Constraints
- **No downloads**: All models and data pre-cached in HuggingFace cache.
- **No mesh retrieval**: --export_layout_only skips get_textured_objects().
- **No rendering**: No Blender calls; visualization disabled.
- **No additional dependencies**: shapely already installed in instructscene_full.

## Key Implementation Files
- `src/ablation/evaluators.py` — Overlap, SG-layout consistency, bounds proxy
- `src/ablation/repairers.py` — Overlap reduction with 3-level SG guard
- `src/ablation/io.py` — Data loading/saving
- `src/generate_sg.py` — Modified with --export_layout_only flag (from export-layout-no-mesh branch)
