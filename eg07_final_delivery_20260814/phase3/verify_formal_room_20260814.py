#!/usr/bin/env python
"""Verify FULL formal output for one room (EG07 Phase 3, 20260814).

Structural checks against the frozen EG-07 contract (no silent fallback, no
accuracy-threshold invention):

  - per_scene count == frozen target for the room,
  - scene_uids present and unique,
  - baseline/repair mesh evidence present for EVERY scene with available==True,
  - object identity (index/class_id/class_name) stable between baseline and
    repair for EVERY scene,
  - mesh_collision_scenes_evaluated == target (collision gate actually ran on
    every scene -> no silent fallback to "always repair"),
  - frozen provenance: seed==0, n_scenes==0, relation_source==parsed,
    repair_strategy==floor_prior, mesh_collision==True, frozen output_suffix,
    frozen checkpoint epochs (VQ per-room, SG2SC 1999, fVQ-VAE 1999).

Usage: verify_formal_room_20260814.py <room> <vq_epoch> <target>
"""
import json
import sys
import glob

ROOM = sys.argv[1]
EPOCH = int(sys.argv[2])
TARGET = int(sys.argv[3])
RT = "/root/autodl-tmp/relation_grounding/eg07_formal_20260813/runtime"
SUFFIX = "floor_prior_max1.8_mesh_p2_close0.75_far1.6"

pat = (f"{RT}/out/{ROOM}_sgdiffusion_vq_objfeat/generated_scenes/"
       f"epoch_{EPOCH:05d}/relation_aware_parsed_{SUFFIX}_eval_cfg1.0_1.0.json")
js = sorted(glob.glob(pat))
if not js:
    print(f"[FAIL] {ROOM}: no formal result JSON at {pat}")
    sys.exit(1)
p = js[-1]
d = json.load(open(p))

ok = True
def chk(name, cond):
    global ok
    print(f"  {name}: {'OK' if cond else 'FAIL'}")
    if not cond:
        ok = False

print(f"[{ROOM}] target={TARGET} json={p}")

# schema
for key in ("args", "metrics", "scores", "per_scene"):
    chk(f"schema has {key}", key in d)

sc = d.get("per_scene", [])
chk(f"per_scene_count == {TARGET}", len(sc) == TARGET)
if len(sc) != TARGET:
    print(f"[FAIL] {ROOM}: per_scene={len(sc)} != {TARGET}")
    sys.exit(1)

# scene_uids present + unique
uids = [s.get("scene_uid") for s in sc]
chk("all scene_uid present", all(u is not None and str(u).strip() != "" for u in uids))
chk(f"scene_uids unique == {TARGET}", len({str(u) for u in uids}) == TARGET)

# per-scene structural invariants
all_lm_avail = all((s.get("layout_mesh_collision") or {}).get("available") is True for s in sc)
all_rm_avail = all((s.get("repair_mesh_collision") or {}).get("available") is True for s in sc)
chk("layout_mesh available==True (all scenes)", all_lm_avail)
chk("repair_mesh available==True (all scenes)", all_rm_avail)
chk("layout_mesh evidence non-empty (all scenes)",
    all(isinstance(s.get("layout_mesh_collision"), dict) and bool(s.get("layout_mesh_collision")) for s in sc))
chk("repair_mesh evidence non-empty (all scenes)",
    all(isinstance(s.get("repair_mesh_collision"), dict) and bool(s.get("repair_mesh_collision")) for s in sc))
chk("layout_mesh objects>=1 (all scenes)",
    all((s.get("layout_mesh_collision") or {}).get("objects", 0) >= 1 for s in sc))
chk("repair_mesh objects>=1 (all scenes)",
    all((s.get("repair_mesh_collision") or {}).get("objects", 0) >= 1 for s in sc))

# object identity stable (all scenes)
ident_ok = True
for s in sc:
    lb = s.get("layout_boxes", [])
    rb = s.get("repair_boxes", [])
    if not lb or not rb:
        ident_ok = False
        break
    base = [(b["index"], b["class_id"], b["class_name"]) for b in lb]
    rep = [(b["index"], b["class_id"], b["class_name"]) for b in rb]
    if base != rep:
        ident_ok = False
        break
chk("object identity stable (all scenes)", ident_ok)
chk("layout_boxes non-empty (all scenes)", all(isinstance(s.get("layout_boxes"), list) and len(s["layout_boxes"]) > 0 for s in sc))
chk("repair_boxes non-empty (all scenes)", all(isinstance(s.get("repair_boxes"), list) and len(s["repair_boxes"]) > 0 for s in sc))

# no silent fallback: mesh collision evaluated on every scene
ms = d.get("scores", {})
chk(f"mesh_collision_scenes_evaluated == {TARGET}", ms.get("mesh_collision_scenes_evaluated") == TARGET)

# frozen provenance
args = d.get("args", {})
chk("args.seed == 0", args.get("seed") == 0)
chk("args.n_scenes == 0", args.get("n_scenes") == 0)
chk("args.relation_source == parsed", args.get("relation_source") == "parsed")
chk("args.repair_strategy == floor_prior", args.get("repair_strategy") == "floor_prior")
chk("args.mesh_collision == True", args.get("mesh_collision") is True)
chk("args.output_suffix frozen", args.get("output_suffix") == SUFFIX)
chk("args.repair_passes == 2", args.get("repair_passes") == 2)
chk("args.close_distance == 0.75", args.get("close_distance") == 0.75)
chk("args.far_distance == 1.6", args.get("far_distance") == 1.6)
chk("args.max_repair_move == 1.8", args.get("max_repair_move") == 1.8)
chk("args.repair_overlap_weight == 1.0", args.get("repair_overlap_weight") == 1.0)
chk(f"args.checkpoint_epoch == {EPOCH}", args.get("checkpoint_epoch") == EPOCH)
chk("args.sg2sc_epoch == 1999", args.get("sg2sc_epoch") == 1999)
chk("args.fvqvae_epoch == 1999", args.get("fvqvae_epoch") == 1999)

print(f"[{'PASS' if ok else 'FAIL'}] {ROOM} (per_scene={len(sc)}, mesh_eval={ms.get('mesh_collision_scenes_evaluated')})")
sys.exit(0 if ok else 1)
