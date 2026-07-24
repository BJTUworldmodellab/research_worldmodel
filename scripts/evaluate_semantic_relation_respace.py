#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


PREDICATES = {
    0: "above",
    1: "left",
    2: "front",
    3: "close_left",
    4: "close_front",
    5: "below",
    6: "right",
    7: "behind",
    8: "close_right",
    9: "close_behind",
}

CLASS_NAMES = {
    0: "armchair",
    1: "bookshelf",
    2: "cabinet",
    3: "ceiling_lamp",
    4: "chair",
    5: "children_cabinet",
    6: "coffee_table",
    7: "desk",
    8: "double_bed",
    9: "dressing_chair",
    10: "dressing_table",
    11: "kids_bed",
    12: "nightstand",
    13: "pendant_lamp",
    14: "shelf",
    15: "single_bed",
    16: "sofa",
    17: "stool",
    18: "table",
    19: "tv_stand",
    20: "wardrobe",
}

CLASS_ALIASES = [
    (11, [r"\bkids?\s+bed\b", r"\bchild(?:ren)?'?s?\s+bed\b"]),
    (15, [r"\bsingle\s+bed\b", r"\btwin\s+bed\b"]),
    (8, [r"\bdouble\s+bed\b", r"\bking[- ]?size\s+bed\b", r"\bqueen[- ]?size\s+bed\b", r"\bbed frame\b", r"\bbed\b"]),
    (12, [r"\bnightstand\b", r"\bbedside\b", r"\bside table\b"]),
    (20, [r"\bwardrobe\b", r"\bcloset\b"]),
    (13, [r"\bpendant lamp\b", r"\bhanging lamp\b", r"\bchandelier\b"]),
    (3, [r"\bceiling lamp\b", r"\bceiling light\b"]),
    (1, [r"\bbookshelf\b", r"\bbookcase\b"]),
    (6, [r"\bcoffee table\b"]),
    (19, [r"\btv stand\b", r"\btelevision stand\b"]),
    (10, [r"\bdressing table\b", r"\bvanity\b"]),
    (9, [r"\bdressing chair\b", r"\bvanity chair\b"]),
    (7, [r"\bdesk\b", r"\bcomputer desk\b", r"\bwriting table\b"]),
    (0, [r"\barmchair\b", r"\blounge chair\b"]),
    (4, [r"\bchair\b", r"\bdining chair\b"]),
    (17, [r"\bstool\b", r"\bbench\b", r"\botttoman\b", r"\bottoman\b"]),
    (16, [r"\bsofa\b", r"\bcouch\b", r"\bchaise\b"]),
    (2, [r"\bcabinet\b", r"\bdresser\b", r"\bchest of drawers\b"]),
    (14, [r"\bshelf\b", r"\bshelving\b"]),
    (18, [r"\btable\b"]),
]


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    count = 0
    for rel in map(tuple, target):
        if rel in pred:
            count += 1
            pred.remove(rel)
    return count


def norm_text(*parts):
    return " ".join(str(p or "").lower().replace("_", " ") for p in parts)


def classify_respace_object(obj):
    text = norm_text(
        obj.get("prompt"),
        obj.get("desc"),
        obj.get("sampled_asset_desc"),
    )
    for class_id, patterns in CLASS_ALIASES:
        for pattern in patterns:
            if re.search(pattern, text):
                return class_id, CLASS_NAMES[class_id], pattern
    return None, None, None


def load_original(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes = data["per_scene"]
    rel_total = 0
    baseline_correct = 0
    repaired_correct = 0
    by_pred = defaultdict(lambda: Counter(total=0, baseline_correct=0, repaired_correct=0))
    for scene in scenes:
        selected = [tuple(r) for r in scene.get("selected_relations", []) if int(r[1]) in PREDICATES]
        layout = [tuple(r) for r in scene.get("layout_relations", [])]
        repair = [tuple(r) for r in scene.get("repair_relations", [])]
        rel_total += len(selected)
        baseline_correct += exact_count(selected, layout)
        repaired_correct += exact_count(selected, repair)
        for rel in selected:
            pred = int(rel[1])
            by_pred[pred]["total"] += 1
            by_pred[pred]["baseline_correct"] += int(rel in layout)
            by_pred[pred]["repaired_correct"] += int(rel in repair)
    return data, {
        "scene_count": len(scenes),
        "target_relations": rel_total,
        "baseline_correct": baseline_correct,
        "repaired_correct": repaired_correct,
        "baseline_acc": baseline_correct / max(rel_total, 1),
        "repaired_acc": repaired_correct / max(rel_total, 1),
        "by_predicate": by_pred,
    }


def respace_box(obj, idx):
    pos = obj.get("pos") or [0.0, 0.0, 0.0]
    size = obj.get("size") or obj.get("sampled_asset_size") or [0.0, 0.0, 0.0]
    class_id, class_name, matched_pattern = classify_respace_object(obj)
    return {
        "index": idx,
        "class_id": class_id,
        "class_name": class_name,
        "matched_pattern": matched_pattern,
        "text": norm_text(obj.get("prompt"), obj.get("desc"), obj.get("sampled_asset_desc")),
        "x": float(pos[0]),
        "y": float(pos[1]),
        "z": float(pos[2]),
        "sx": abs(float(size[0])),
        "sy": abs(float(size[1])),
        "sz": abs(float(size[2])),
    }


def horizontal_distance(a, b):
    return math.hypot(a["x"] - b["x"], a["z"] - b["z"])


def relation_holds(a, pred, b, close_threshold=0.75, eps=1e-4):
    if pred == 0:
        return a["y"] > b["y"] + eps
    if pred == 5:
        return a["y"] < b["y"] - eps
    if pred == 1:
        return a["x"] < b["x"] - eps
    if pred == 6:
        return a["x"] > b["x"] + eps
    if pred == 2:
        return a["z"] > b["z"] + eps
    if pred == 7:
        return a["z"] < b["z"] - eps
    if pred == 3:
        return a["x"] < b["x"] - eps and horizontal_distance(a, b) <= close_threshold
    if pred == 4:
        return a["z"] > b["z"] + eps and horizontal_distance(a, b) <= close_threshold
    if pred == 8:
        return a["x"] > b["x"] + eps and horizontal_distance(a, b) <= close_threshold
    if pred == 9:
        return a["z"] < b["z"] - eps and horizontal_distance(a, b) <= close_threshold
    return False


def score_relation(boxes, rel, close_threshold=0.75):
    subj_class, pred, obj_class = map(int, rel)
    subj = [b for b in boxes if b["class_id"] == subj_class]
    obj = [b for b in boxes if b["class_id"] == obj_class]
    if not subj or not obj:
        return False, "missing_class"
    for a in subj:
        for b in obj:
            if a["index"] == b["index"]:
                continue
            if relation_holds(a, pred, b, close_threshold=close_threshold):
                return True, "ok"
    return False, "relation_not_satisfied"


def scene_index_from_path(path):
    stem = Path(path).stem
    try:
        return int(stem.split("_", 1)[0])
    except Exception:
        return None


def load_respace_scene(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [respace_box(obj, idx) for idx, obj in enumerate(data.get("objects", []))]


def evaluate_respace_dir(name, root, original_scenes, close_threshold=0.75):
    root = Path(root)
    detail_rows = []
    summary = Counter(files=0, matched_files=0, target_relations=0, correct=0, missing_class=0, relation_not_satisfied=0)
    by_pred = defaultdict(lambda: Counter(total=0, correct=0, missing_class=0, relation_not_satisfied=0))
    class_hits = Counter()
    class_total = Counter()

    for path in sorted(root.rglob("*.json")):
        scene_idx = scene_index_from_path(path)
        if scene_idx is None or scene_idx >= len(original_scenes):
            continue
        summary["files"] += 1
        summary["matched_files"] += 1
        scene = original_scenes[scene_idx]
        targets = [tuple(r) for r in scene.get("selected_relations", []) if int(r[1]) in PREDICATES]
        boxes = load_respace_scene(path)
        present = {b["class_id"] for b in boxes if b["class_id"] is not None}
        for b in boxes:
            if b["class_id"] is not None:
                class_hits[b["class_name"]] += 1
        for rel in targets:
            subj_class, pred, obj_class = map(int, rel)
            summary["target_relations"] += 1
            by_pred[pred]["total"] += 1
            class_total[CLASS_NAMES.get(subj_class, str(subj_class))] += 1
            class_total[CLASS_NAMES.get(obj_class, str(obj_class))] += 1
            ok, reason = score_relation(boxes, rel, close_threshold=close_threshold)
            summary["correct"] += int(ok)
            by_pred[pred]["correct"] += int(ok)
            if not ok:
                summary[reason] += 1
                by_pred[pred][reason] += 1
            detail_rows.append({
                "method": name,
                "path": str(path),
                "scene_index": scene_idx,
                "text": scene.get("text", ""),
                "subject_class": CLASS_NAMES.get(subj_class, str(subj_class)),
                "predicate_id": pred,
                "predicate": PREDICATES[pred],
                "object_class": CLASS_NAMES.get(obj_class, str(obj_class)),
                "ok": int(ok),
                "failure_reason": "" if ok else reason,
                "generated_objects": len(boxes),
                "mapped_classes": "|".join(sorted(CLASS_NAMES[c] for c in present if c in CLASS_NAMES)),
            })

    summary_dict = dict(summary)
    summary_dict["method"] = name
    summary_dict["eligible_relations"] = summary["target_relations"] - summary["missing_class"]
    summary_dict["coverage_rate"] = summary_dict["eligible_relations"] / max(summary["target_relations"], 1)
    summary_dict["relation_acc"] = summary["correct"] / max(summary["target_relations"], 1)
    summary_dict["conditional_relation_acc"] = summary["correct"] / max(summary_dict["eligible_relations"], 1)
    summary_dict["by_predicate"] = by_pred
    summary_dict["class_hits"] = class_hits
    summary_dict["class_total"] = class_total
    return summary_dict, detail_rows


def matched_scene_indices(root, original_scene_count):
    indices = []
    for path in sorted(Path(root).rglob("*.json")):
        scene_idx = scene_index_from_path(path)
        if scene_idx is not None and scene_idx < original_scene_count:
            indices.append(scene_idx)
    return indices


def evaluate_original_indices(name, original_scenes, indices, relation_key):
    rel_total = 0
    correct = 0
    by_pred = defaultdict(lambda: Counter(total=0, correct=0))
    for scene_idx in indices:
        scene = original_scenes[scene_idx]
        selected = [tuple(r) for r in scene.get("selected_relations", []) if int(r[1]) in PREDICATES]
        predicted = [tuple(r) for r in scene.get(relation_key, [])]
        rel_total += len(selected)
        correct += exact_count(selected, predicted)
        predicted_set = set(predicted)
        for rel in selected:
            pred = int(rel[1])
            by_pred[pred]["total"] += 1
            by_pred[pred]["correct"] += int(rel in predicted_set)
    return {
        "method": name,
        "scene_count": len(indices),
        "target_relations": rel_total,
        "correct": correct,
        "relation_acc": correct / max(rel_total, 1),
        "coverage_rate": 1.0,
        "conditional_relation_acc": correct / max(rel_total, 1),
        "by_predicate": by_pred,
    }


def flatten_pred_rows(method, by_pred, baseline=False):
    rows = []
    for pred, counts in sorted(by_pred.items()):
        total = counts["total"]
        if baseline:
            rows.append({
                "method": "original_baseline_layout",
                "predicate_id": pred,
                "predicate": PREDICATES.get(pred, str(pred)),
                "total": total,
                "correct": counts["baseline_correct"],
                "accuracy": counts["baseline_correct"] / max(total, 1),
                "coverage_rate": 1.0,
                "conditional_accuracy": counts["baseline_correct"] / max(total, 1),
                "missing_class": "",
                "relation_not_satisfied": "",
            })
            rows.append({
                "method": "original_repaired_floor_prior",
                "predicate_id": pred,
                "predicate": PREDICATES.get(pred, str(pred)),
                "total": total,
                "correct": counts["repaired_correct"],
                "accuracy": counts["repaired_correct"] / max(total, 1),
                "coverage_rate": 1.0,
                "conditional_accuracy": counts["repaired_correct"] / max(total, 1),
                "missing_class": "",
                "relation_not_satisfied": "",
            })
        else:
            rows.append({
                "method": method,
                "predicate_id": pred,
                "predicate": PREDICATES.get(pred, str(pred)),
                "total": total,
            "correct": counts["correct"],
            "accuracy": counts["correct"] / max(total, 1),
            "coverage_rate": (total - counts["missing_class"]) / max(total, 1),
            "conditional_accuracy": counts["correct"] / max(total - counts["missing_class"], 1),
            "missing_class": counts["missing_class"],
            "relation_not_satisfied": counts["relation_not_satisfied"],
        })
    return rows


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def serializable(obj):
    if isinstance(obj, Counter):
        return dict(obj)
    if isinstance(obj, defaultdict):
        return {k: serializable(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serializable(v) for v in obj]
    return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-json", required=True)
    parser.add_argument("--respace-full-dir", required=True)
    parser.add_argument("--respace-add-dir", required=True)
    parser.add_argument("--out-summary-csv", required=True)
    parser.add_argument("--out-predicate-csv", required=True)
    parser.add_argument("--out-detail-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--close-threshold", type=float, default=0.75)
    args = parser.parse_args()

    original, original_summary = load_original(args.original_json)
    scenes = original["per_scene"]
    full_summary, full_details = evaluate_respace_dir(
        "qwen_respace_full_scene_n54",
        args.respace_full_dir,
        scenes,
        close_threshold=args.close_threshold,
    )
    add_summary, add_details = evaluate_respace_dir(
        "qwen_respace_add_only_n54",
        args.respace_add_dir,
        scenes,
        close_threshold=args.close_threshold,
    )
    matched_indices = matched_scene_indices(args.respace_full_dir, len(scenes))
    original_matched_baseline = evaluate_original_indices(
        "original_baseline_layout_matched_n54x3",
        scenes,
        matched_indices,
        "layout_relations",
    )
    original_matched_repaired = evaluate_original_indices(
        "original_repaired_floor_prior_matched_n54x3",
        scenes,
        matched_indices,
        "repair_relations",
    )

    summary_rows = [
        {
            "method": "original_baseline_layout",
            "scene_count": original_summary["scene_count"],
            "matched_files": "",
            "target_relations": original_summary["target_relations"],
            "correct": original_summary["baseline_correct"],
            "relation_acc": original_summary["baseline_acc"],
            "coverage_rate": 1.0,
            "conditional_relation_acc": original_summary["baseline_acc"],
            "missing_class": "",
            "relation_not_satisfied": "",
            "note": "official stored layout_relations exact match",
        },
        {
            "method": "original_repaired_floor_prior",
            "scene_count": original_summary["scene_count"],
            "matched_files": "",
            "target_relations": original_summary["target_relations"],
            "correct": original_summary["repaired_correct"],
            "relation_acc": original_summary["repaired_acc"],
            "coverage_rate": 1.0,
            "conditional_relation_acc": original_summary["repaired_acc"],
            "missing_class": "",
            "relation_not_satisfied": "",
            "note": "official stored repair_relations exact match",
        },
        {
            "method": original_matched_baseline["method"],
            "scene_count": original_matched_baseline["scene_count"],
            "matched_files": original_matched_baseline["scene_count"],
            "target_relations": original_matched_baseline["target_relations"],
            "correct": original_matched_baseline["correct"],
            "relation_acc": original_matched_baseline["relation_acc"],
            "coverage_rate": original_matched_baseline["coverage_rate"],
            "conditional_relation_acc": original_matched_baseline["conditional_relation_acc"],
            "missing_class": "",
            "relation_not_satisfied": "",
            "note": "official stored layout_relations, repeated over the same ReSpace filename indices",
        },
        {
            "method": original_matched_repaired["method"],
            "scene_count": original_matched_repaired["scene_count"],
            "matched_files": original_matched_repaired["scene_count"],
            "target_relations": original_matched_repaired["target_relations"],
            "correct": original_matched_repaired["correct"],
            "relation_acc": original_matched_repaired["relation_acc"],
            "coverage_rate": original_matched_repaired["coverage_rate"],
            "conditional_relation_acc": original_matched_repaired["conditional_relation_acc"],
            "missing_class": "",
            "relation_not_satisfied": "",
            "note": "official stored repair_relations, repeated over the same ReSpace filename indices",
        },
    ]
    for item in [full_summary, add_summary]:
        summary_rows.append({
            "method": item["method"],
            "scene_count": item["files"],
            "matched_files": item["matched_files"],
            "target_relations": item["target_relations"],
            "correct": item["correct"],
            "relation_acc": item["relation_acc"],
            "coverage_rate": item["coverage_rate"],
            "conditional_relation_acc": item["conditional_relation_acc"],
            "missing_class": item["missing_class"],
            "relation_not_satisfied": item["relation_not_satisfied"],
            "note": "heuristic class-name matching plus axis relation scoring against original scene index targets",
        })

    predicate_rows = []
    predicate_rows.extend(flatten_pred_rows("original", original_summary["by_predicate"], baseline=True))
    predicate_rows.extend(flatten_pred_rows(original_matched_baseline["method"], original_matched_baseline["by_predicate"]))
    predicate_rows.extend(flatten_pred_rows(original_matched_repaired["method"], original_matched_repaired["by_predicate"]))
    predicate_rows.extend(flatten_pred_rows(full_summary["method"], full_summary["by_predicate"]))
    predicate_rows.extend(flatten_pred_rows(add_summary["method"], add_summary["by_predicate"]))

    detail_rows = full_details + add_details
    write_csv(args.out_summary_csv, summary_rows)
    write_csv(args.out_predicate_csv, predicate_rows)
    write_csv(args.out_detail_csv, detail_rows)
    out = {
        "methodology": {
            "respace_matching": "Each ReSpace JSON filename index is matched to the original per_scene index. The 54-scene sequence is repeated for each seed directory.",
            "class_matching": "Keyword aliases over prompt/desc/sampled_asset_desc.",
            "relation_scoring": "Axis tests over object centers: x for left/right, z for front/behind, y for above/below; close predicates also require horizontal distance <= close_threshold.",
            "close_threshold": args.close_threshold,
            "caveat": "Original methods use stored relation evaluator outputs; ReSpace is scored with a transparent heuristic adapter because its JSON does not store target relation triples.",
        },
        "summary": summary_rows,
        "predicate_rows": predicate_rows,
        "respace_full": serializable(full_summary),
        "respace_add": serializable(add_summary),
        "original_matched_baseline": serializable(original_matched_baseline),
        "original_matched_repaired": serializable(original_matched_repaired),
    }
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"summary": summary_rows, "outputs": {
        "summary_csv": args.out_summary_csv,
        "predicate_csv": args.out_predicate_csv,
        "detail_csv": args.out_detail_csv,
        "json": args.out_json,
    }}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
