import json
from pathlib import Path

from render_real_mesh_showcase import annotate_pair, exact_count, render_layout


OUT = Path("/root/RelationAwareInstructScene/outputs/floor_prior_showcase")

JSONS = {
    "bedroom": "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "livingroom": "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/livingroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01459/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "diningroom": "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01239/relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
}


def mesh_pairs(scene, key):
    mesh = scene.get(key) or {}
    return mesh.get("collision_pairs", 10**9)


def has_assets(scene):
    return scene.get("object_model_jids") and scene.get("repair_object_model_jids")


def select_examples(data, limit):
    candidates = []
    for idx, scene in enumerate(data["per_scene"]):
        if not has_assets(scene):
            continue
        selected = scene["selected_relations"]
        before_score = exact_count(selected, scene["layout_relations"])
        after_score = exact_count(selected, scene["repair_relations"])
        gain = after_score - before_score
        if gain <= 0:
            continue
        before_pairs = mesh_pairs(scene, "layout_mesh_collision")
        after_pairs = mesh_pairs(scene, "repair_mesh_collision")
        if after_pairs > before_pairs:
            continue
        move = float(scene.get("repair_stats", {}).get("avg_movement", 0.0) or 0.0)
        candidates.append((gain, -after_pairs, -move, idx, before_score, after_score, before_pairs, after_pairs))
    candidates.sort(reverse=True)
    return candidates[:limit]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for room, json_path in JSONS.items():
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        selected = select_examples(data, limit=5)
        print(room, "selected", selected)
        for _gain, _neg_pairs, _neg_move, idx, _bs, _as, _bp, _ap in selected:
            scene = data["per_scene"][idx]
            before = OUT / f"{room}_{idx:04d}_before.png"
            after = OUT / f"{room}_{idx:04d}_after.png"
            combined = OUT / f"{room}_{idx:04d}_comparison.png"
            print("render", room, idx, "before")
            _before_path, before_pairs = render_layout(scene, "before", before)
            print("render", room, idx, "after")
            _after_path, after_pairs = render_layout(scene, "after", after)
            annotate_pair(before, after, scene, room, idx, combined, before_pairs, after_pairs)
            manifest.append({
                "room": room,
                "idx": idx,
                "text": scene["text"],
                "before": str(before),
                "after": str(after),
                "combined": str(combined),
                "beforeScore": exact_count(scene["selected_relations"], scene["layout_relations"]),
                "afterScore": exact_count(scene["selected_relations"], scene["repair_relations"]),
                "total": len(scene["selected_relations"]),
                "beforePairs": before_pairs if before_pairs is not None else mesh_pairs(scene, "layout_mesh_collision"),
                "afterPairs": after_pairs if after_pairs is not None else mesh_pairs(scene, "repair_mesh_collision"),
                "variant": "floor_prior_max1.8_mesh_p2_close0.75_far1.6",
            })
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(OUT / "manifest.json")


if __name__ == "__main__":
    main()
