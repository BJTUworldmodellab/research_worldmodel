#!/usr/bin/env python
"""EG07 Phase 3 formal summary + GO/NO-GO table (2026-08-14).

Reads the three frozen source JSONs, the exported formal_candidate layouts.json,
and the independent validation_recheck.json, then emits a room-level + total
metric table and a structural GO/NO-GO table.

Thresholds are FROZEN structural contract only (room counts 162/192/177,
531 scenes / 1062 layouts, mesh evidence full coverage, no silent fallback,
object identity stability, validator PASS, provenance complete). NO accuracy
thresholds are invented and NO numbers are written into the paper main table.
"""
import json
import glob
import sys

RT = "/root/autodl-tmp/relation_grounding/eg07_formal_20260813/runtime"
RUN = "/root/autodl-tmp/relation_grounding/eg07_formal_20260813"
SUFFIX = "floor_prior_max1.8_mesh_p2_close0.75_far1.6"
REPO = "/root/autodl-tmp/relation_grounding/code/eg07-full-export"
LAYOUTS = f"{RUN}/results/eg07/formal_candidate/layouts.json"
RECHECK = f"{RUN}/results/eg07/formal_candidate/validation_recheck.json"

ROOMS = [
    ("bedroom", 1999, 162),
    ("livingroom", 1459, 192),
    ("diningroom", 1239, 177),
]
FROZEN_CONFIG_SHA = "052ACE5B295348483CE9B6110B5BD7933235424A55CC2108C966431E516829E2"
CODE_COMMIT = "3a167d813d74ab18df8762d57ff3b4a47789e3af"


def load_source(room, epoch):
    pat = (f"{RT}/out/{room}_sgdiffusion_vq_objfeat/generated_scenes/"
           f"epoch_{epoch:05d}/relation_aware_parsed_{SUFFIX}_eval_cfg1.0_1.0.json")
    js = sorted(glob.glob(pat))
    if not js:
        raise SystemExit(f"[BLOCKED] missing source JSON for {room}: {pat}")
    return json.load(open(js[-1]))


checks = []
def go(name, cond):
    checks.append((name, bool(cond)))


def fmt(v, nd=4):
    try:
        return f"{float(v):.{nd}f}"
    except Exception:
        return str(v)


room_rows = []
mesh_all_ok = True
fallback_all_ok = True
identity_all_ok = True
total_scenes = 0

for room, epoch, target in ROOMS:
    d = load_source(room, epoch)
    sc = d["per_scene"]
    scores = d.get("scores", {})
    args = d.get("args", {})
    total_scenes += len(sc)

    mesh_eval = scores.get("mesh_collision_scenes_evaluated", 0)
    lm_avail = all((s.get("layout_mesh_collision") or {}).get("available") is True for s in sc)
    rm_avail = all((s.get("repair_mesh_collision") or {}).get("available") is True for s in sc)
    ident_ok = all(
        [(b["index"], b["class_id"], b["class_name"]) for b in s.get("layout_boxes", [])]
        == [(b["index"], b["class_id"], b["class_name"]) for b in s.get("repair_boxes", [])]
        for s in sc
    )
    mesh_all_ok &= lm_avail and rm_avail
    identity_all_ok &= ident_ok
    fallback_all_ok &= (mesh_eval == target)

    room_rows.append((room, target, len(sc), mesh_eval,
                      fmt(scores.get("baseline_relation_acc")),
                      fmt(scores.get("repaired_relation_acc")),
                      fmt(scores.get("avg_repair_movement")),
                      fmt(scores.get("layout_mesh_collision_pair_rate")),
                      fmt(scores.get("repair_mesh_collision_pair_rate")),
                      lm_avail and rm_avail, ident_ok, (mesh_eval == target)))

    go(f"{room}: per_scene == {target}", len(sc) == target)
    go(f"{room}: mesh evidence available (all scenes)", lm_avail and rm_avail)
    go(f"{room}: object identity stable (all scenes)", ident_ok)
    go(f"{room}: no silent fallback (mesh_eval == {target})", mesh_eval == target)

# ---- export + recheck artifacts ----
layouts = json.load(open(LAYOUTS))
recheck = json.load(open(RECHECK))
prov = layouts.get("provenance", {})
summary = layouts.get("summary", {})
gate_by_room = summary.get("gate_decision_by_room", {})
rel_status = summary.get("relation_export_status", {})

layout_count = len(layouts.get("layouts", []))
go("total scenes == 531", total_scenes == 531)
go("total layouts == 1062", layout_count == 1062)

validator_pass = recheck.get("status") == "PASS"
go("independent validator status == PASS", validator_pass)

prov_ok = (
    prov.get("artifact_status") == "formal_candidate"
    and prov.get("code_commit") == CODE_COMMIT
    and prov.get("source_config_sha256") == FROZEN_CONFIG_SHA
    and prov.get("source_config_git_clean") is True
)
go("provenance complete (formal_candidate, commit, config SHA, git-clean)", prov_ok)

# gate counts reconciled: repair + fallback == scene count per room
gate_reconciled = True
for room, _epoch, target in ROOMS:
    g = gate_by_room.get(room, {})
    n = int(g.get("repair", 0)) + int(g.get("fallback_baseline", 0))
    if n != target:
        gate_reconciled = False
    go(f"{room}: gate decisions sum == {target} (repair+fallback)", n == target)
go("gate counts reconciled (no scene skipped in gate)", gate_reconciled)

all_go = all(cond for _n, cond in checks)

# ---- emit markdown ----
print("\n## Phase 3 formal summary (2026-08-14)")
print("\n### Room-level metrics (frozen fair-comparison order)\n")
print("| room | target | per_scene | mesh_eval | base_rel_acc | repair_rel_acc | avg_move | base_mesh_pair | repair_mesh_pair | mesh_avail | ident_stable | no_fallback |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in room_rows:
    room, target, n, me, bra, rra, am, bmp, rmp, ma, ident, nf = r
    print(f"| {room} | {target} | {n} | {me} | {bra} | {rra} | {am} | {bmp} | {rmp} | {ma} | {ident} | {nf} |")

print("\n### Total")
print(f"- scenes: {total_scenes} / 531")
print(f"- layouts: {layout_count} / 1062")
print(f"- target_relations: {sum(rel_status.values())}")
print(f"- relation_export_status: {rel_status}")
print(f"- gate_decision_by_room: {gate_by_room}")

print("\n### GO / NO-GO (frozen structural contract)\n")
print("| check | result | GO/NO-GO |")
print("|---|---|---|")
for name, cond in checks:
    print(f"| {name} | {'PASS' if cond else 'FAIL'} | {'GO' if cond else 'NO-GO'} |")

print(f"\n### VERDICT: {'GO' if all_go else 'NO-GO'}")
sys.exit(0 if all_go else 1)
