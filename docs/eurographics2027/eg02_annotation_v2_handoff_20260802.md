# EG-02 Annotation V2 Handoff

Date: 2026-08-02

Purpose: provide a clearer real-mesh annotation table after annotators reported
that the earlier views were hard to judge and that automatic repair labels did
not always match direct coordinate checks.

## Local Package

```text
annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802_v2.zip
```

This package contains:

```text
images/                                            90 real-mesh JPG images
eg02_human_review_sample_real_mesh_images_v2.csv   v2 annotation table
eg02_annotation_v2_alignment_audit.csv             rows needing special care
README_v2_for_annotator.md                         annotator instructions
manifest.json                                      render manifest
```

## V2 Coordinate Rule

The v2 table exposes coordinate differences directly:

```text
dx_subject_minus_object
dy_subject_minus_object
dz_subject_minus_object
distance_xz
coord_rule_label
```

Rules used by `coord_rule_label`:

```text
left        dx < 0
right       dx > 0
in front of dz > 0
behind      dz < 0
above       dy > 0
below       dy < 0
close to    distance_xz <= 0.75
```

## Alignment Audit

The v2 generation found:

```text
rows = 90
pair_alignment_ok = 84
alignment_audit_rows = 24
```

The audit rows include:

```text
missing_pair
coord_repair_disagree
```

For these rows, annotators should rely on the real mesh image and coordinate
columns rather than copying `repair_relation_exact_present`.

## Reproduction Scripts

```text
scripts/build_eg02_real_mesh_annotation_v2.py
scripts/check_eg02_annotation_v2_alignment.py
```

