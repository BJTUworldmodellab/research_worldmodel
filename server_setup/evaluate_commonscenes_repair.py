import argparse
import json
import math
from pathlib import Path


PREDICATES = [
    "in",
    "left",
    "right",
    "front",
    "behind",
    "close by",
    "above",
    "standing on",
    "bigger than",
    "smaller than",
    "taller than",
    "shorter than",
    "symmetrical to",
    "same style as",
    "same super category as",
    "same material as",
]


METRIC_KEYS = [
    "left",
    "right",
    "front",
    "behind",
    "bigger than",
    "smaller than",
    "taller than",
    "shorter than",
    "standing on",
    "close by",
    "symmetrical to",
]


def close_distance(a, b):
    # Conservative AABB gap proxy in the x-z footprint plane.
    ax0, az0, ax1, az1 = a[3] - a[0] / 2, a[5] - a[2] / 2, a[3] + a[0] / 2, a[5] + a[2] / 2
    bx0, bz0, bx1, bz1 = b[3] - b[0] / 2, b[5] - b[2] / 2, b[3] + b[0] / 2, b[5] + b[2] / 2
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dz = max(bz0 - az1, az0 - bz1, 0.0)
    return math.sqrt(dx * dx + dz * dz)


def footprint_iou(a, b):
    ax0, az0, ax1, az1 = a[3] - a[0] / 2, a[5] - a[2] / 2, a[3] + a[0] / 2, a[5] + a[2] / 2
    bx0, bz0, bx1, bz1 = b[3] - b[0] / 2, b[5] - b[2] / 2, b[3] + b[0] / 2, b[5] + b[2] / 2
    ix0, iz0 = max(ax0, bx0), max(az0, bz0)
    ix1, iz1 = min(ax1, bx1), min(az1, bz1)
    inter = max(ix1 - ix0, 0.0) * max(iz1 - iz0, 0.0)
    area_a = max(ax1 - ax0, 0.0) * max(az1 - az0, 0.0)
    area_b = max(bx1 - bx0, 0.0) * max(bz1 - bz0, 0.0)
    denom = area_a + area_b - inter
    return inter / denom if denom else 0.0


def satisfies(boxes, triple, strict=True):
    s, p, o = triple
    if s >= len(boxes) or o >= len(boxes) or p >= len(PREDICATES):
        return None
    bs, bo = boxes[s], boxes[o]
    pred = PREDICATES[p]
    if strict and pred in {"left", "right", "front", "behind"} and footprint_iou(bs, bo) > 0.3:
        return False
    if pred == "left":
        return bs[5] - bo[5] < -0.05
    if pred == "right":
        return bs[5] - bo[5] > 0.05
    if pred == "front":
        return bs[3] - bo[3] > -0.05
    if pred == "behind":
        return bs[3] - bo[3] < 0.05
    if pred == "bigger than":
        vs, vo = bs[0] * bs[1] * bs[2], bo[0] * bo[1] * bo[2]
        return (vs - vo) / vs >= 0.15 if vs else False
    if pred == "smaller than":
        vs, vo = bs[0] * bs[1] * bs[2], bo[0] * bo[1] * bo[2]
        return (vs - vo) / vs <= -0.15 if vs else False
    if pred == "taller than":
        hs, ho = bs[4] + bs[1], bo[4] + bo[1]
        return (hs - ho) / hs >= 0.1 if hs else False
    if pred == "shorter than":
        hs, ho = bs[4] + bs[1], bo[4] + bo[1]
        return (hs - ho) / hs <= -0.1 if hs else False
    if pred == "standing on":
        return abs(bs[4] - bo[4]) < 0.04
    if pred == "close by":
        return close_distance(bs, bo) <= 0.45
    if pred == "symmetrical to":
        candidates = [(-bs[3], -bs[5]), (-bs[3], bs[5]), (bs[3], -bs[5])]
        return min(math.dist(c, (bo[3], bo[5])) for c in candidates) < 0.45
    return None


def repair_once(boxes, triples, step=0.65):
    out = [list(b) for b in boxes]
    edits = 0
    movement = 0.0
    for tri in triples:
        s, p, o = tri
        if s >= len(out) or o >= len(out) or p >= len(PREDICATES):
            continue
        pred = PREDICATES[p]
        if pred not in {"left", "right", "front", "behind", "close by"}:
            continue
        if satisfies(out, tri):
            continue
        old_x, old_z = out[s][3], out[s][5]
        ox, oz = out[o][3], out[o][5]
        if pred == "left":
            out[s][5] = oz - max(step, (out[s][2] + out[o][2]) * 0.35)
        elif pred == "right":
            out[s][5] = oz + max(step, (out[s][2] + out[o][2]) * 0.35)
        elif pred == "front":
            out[s][3] = ox + max(step, (out[s][0] + out[o][0]) * 0.35)
        elif pred == "behind":
            out[s][3] = ox - max(step, (out[s][0] + out[o][0]) * 0.35)
        elif pred == "close by":
            out[s][3] = ox + min(step * 0.5, max(out[o][0], 0.1))
            out[s][5] = oz
        edits += 1
        movement += math.dist((old_x, old_z), (out[s][3], out[s][5]))
    return out, edits, movement


def score_dataset(data):
    totals = {k: {"ok": 0, "total": 0} for k in METRIC_KEYS + ["total"]}
    for scene in data.values():
        boxes = scene["boxes_denormalized_xyzwhd"]
        for tri in scene["triples_s_p_o"]:
            if tri[1] >= len(PREDICATES):
                continue
            pred = PREDICATES[tri[1]]
            ok = satisfies(boxes, tri)
            if ok is None or pred not in totals:
                continue
            totals[pred]["total"] += 1
            totals[pred]["ok"] += int(ok)
            totals["total"]["total"] += 1
            totals["total"]["ok"] += int(ok)
    return totals


def run_repair(data, passes):
    repaired = {}
    edits = 0
    movement = 0.0
    for key, scene in data.items():
        boxes = [list(b) for b in scene["boxes_denormalized_xyzwhd"]]
        for _ in range(passes):
            boxes, e, m = repair_once(boxes, scene["triples_s_p_o"])
            edits += e
            movement += m
        new_scene = dict(scene)
        new_scene["boxes_denormalized_xyzwhd"] = boxes
        repaired[key] = new_scene
    return repaired, edits, movement


def summarize(totals):
    out = {}
    for key, value in totals.items():
        total = value["total"]
        out[key] = {
            "ok": value["ok"],
            "total": total,
            "acc": value["ok"] / total if total else None,
        }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--passes", type=int, default=2)
    args = parser.parse_args()

    data = json.load(open(args.input))
    base = summarize(score_dataset(data))
    repaired, edits, movement = run_repair(data, args.passes)
    repaired_scores = summarize(score_dataset(repaired))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.input).stem
    repaired_path = out_dir / f"{stem}_repair_p{args.passes}.json"
    summary_path = out_dir / f"{stem}_repair_p{args.passes}_summary.json"
    json.dump(repaired, open(repaired_path, "w"), indent=2)
    summary = {
        "input": args.input,
        "repaired_boxes": str(repaired_path),
        "scenes": len(data),
        "passes": args.passes,
        "edits": edits,
        "movement_xz": movement,
        "baseline": base,
        "repaired": repaired_scores,
    }
    json.dump(summary, open(summary_path, "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
