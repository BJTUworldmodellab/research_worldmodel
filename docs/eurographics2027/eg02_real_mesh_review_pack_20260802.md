# EG-02 Real Mesh Review Pack

Date: 2026-08-02

Purpose: replace the earlier top-down SVG review pack because annotators
reported that most SVG views were hard to judge.

## Render Type

The new pack uses real 3D-FUTURE meshes from AutoDL:

```text
/root/autodl-tmp/RelationAwareInstructScene/raw_data/3D-FRONT/3D-FUTURE-model
```

Each annotation image contains three views:

```text
isometric
top
front
```

Color convention:

```text
blue = subject object
orange = reference object
dark arrow = reference object to subject object
```

## Local Pack

The local handoff pack is:

```text
annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802.zip
```

Extracted folder:

```text
annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802/extracted
```

Contents:

```text
images/                                           90 JPG review images
eg02_human_review_sample_real_mesh_images.csv     annotation table with image paths
manifest.json                                     render manifest
README_for_annotator.md                           short annotator instructions
```

The full-resolution PNG render archive was not kept locally because transfer
from AutoDL was unstable. A compressed JPG pack was generated from the same
real mesh renders and verified locally.

## Remote Cleanup

The temporary AutoDL render directory was deleted after the JPG pack was
downloaded and verified:

```text
/root/autodl-tmp/eg02_real_render_tmp
```

Original experiment JSONs and 3D-FUTURE assets were not deleted.

## Scripts

```text
scripts/render_eg02_human_review_real_mesh.py
scripts/compress_eg02_real_mesh_review_pack.py
```

