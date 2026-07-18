
import os
import argparse
import random
import pickle
import json
import re
from copy import deepcopy

from tqdm import tqdm
import numpy as np
import torch
import trimesh
from torch.utils.data import DataLoader
import torch.nn.functional as F
from diffusers.training_utils import EMAModel

from src.utils.util import *
from src.utils.visualize import get_textured_objects
from src.data import filter_function, get_dataset_raw_and_encoded, get_encoded_dataset
from src.data.threed_future_dataset import ThreedFutureDataset
from src.data.threed_front_dataset_base import trs_to_corners
from src.data.utils_text import compute_loc_rel, reverse_rel, fill_templates
from src.models import model_from_config, ObjectFeatureVQVAE
from src.models.sg2sc_diffusion import Sg2ScDiffusion
from src.models.sg_diffusion_vq_objfeat import scatter_trilist_to_matrix
from src.models.clip_encoders import CLIPTextEncoder


def easy_relation(rel, predicate_types):
    s, p, o = rel
    name = predicate_types[p]
    if "closely" in name:
        return (s, p - 2, o)
    if name not in ["above", "below"]:
        return (s, p + 2, o)
    return rel


def count_matches(target_relations, predicted_relations, predicate_types):
    exact = 0
    easy = 0
    predicted_exact = list(predicted_relations)
    predicted_easy = list(predicted_relations)
    for rel in target_relations:
        rel = tuple(map(int, rel))
        if rel in predicted_exact:
            exact += 1
            predicted_exact.remove(rel)
        easy_rel = easy_relation(rel, predicate_types)
        if rel in predicted_easy:
            easy += 1
            predicted_easy.remove(rel)
        elif easy_rel in predicted_easy:
            easy += 1
            predicted_easy.remove(easy_rel)
    return exact, easy


def graph_relations_from_edges(edges_scene, obj_class_ids, n_object_types, n_predicate_types):
    relations = []
    for idx in range(len(obj_class_ids)):
        if obj_class_ids[idx] == n_object_types:
            continue
        for other_idx in range(idx + 1, len(obj_class_ids)):
            if obj_class_ids[other_idx] == n_object_types:
                continue
            if edges_scene[idx, other_idx] == n_predicate_types:
                continue
            relation_id = int(edges_scene[idx, other_idx].item() if hasattr(edges_scene[idx, other_idx], "item") else edges_scene[idx, other_idx])
            relations.append((int(obj_class_ids[idx]), relation_id, int(obj_class_ids[other_idx])))
            reverse_relation_id = int(edges_scene[other_idx, idx].item() if hasattr(edges_scene[other_idx, idx], "item") else edges_scene[other_idx, idx])
            relations.append((int(obj_class_ids[other_idx]), reverse_relation_id, int(obj_class_ids[idx])))
    return relations


def layout_relations_from_boxes(bbox_scene, obj_class_ids, obj_sizes, dataset):
    relations = []
    cls_dim = dataset.n_object_types + 1
    for idx in range(len(obj_class_ids)):
        if obj_class_ids[idx] == dataset.n_object_types:
            continue
        c1_id = obj_class_ids[idx]
        t1 = bbox_scene[idx, cls_dim:cls_dim + 3]
        r1 = bbox_scene[idx, cls_dim + 6]
        s1 = obj_sizes[idx]
        corners1 = trs_to_corners(t1, r1, s1)
        name1 = dataset.object_types[c1_id]
        for other_idx in range(idx + 1, len(obj_class_ids)):
            if obj_class_ids[other_idx] == dataset.n_object_types:
                continue
            c2_id = obj_class_ids[other_idx]
            t2 = bbox_scene[other_idx, cls_dim:cls_dim + 3]
            r2 = bbox_scene[other_idx, cls_dim + 6]
            s2 = obj_sizes[other_idx]
            corners2 = trs_to_corners(t2, r2, s2)
            name2 = dataset.object_types[c2_id]
            loc_rel_str = compute_loc_rel(corners1, corners2, name1, name2)
            if loc_rel_str is not None:
                relation_id = dataset.predicate_types.index(loc_rel_str)
                relations.append((int(c1_id), int(relation_id), int(c2_id)))
                rev_relation_id = dataset.predicate_types.index(reverse_rel(loc_rel_str))
                relations.append((int(c2_id), int(rev_relation_id), int(c1_id)))
    return relations


def footprint_aabb_from_trs(translation, angle, size):
    corners = np.asarray(trs_to_corners(translation, angle, size))
    corners = corners.reshape(-1, corners.shape[-1])
    if corners.shape[-1] >= 3:
        xs = corners[:, 0]
        zs = corners[:, 2]
    else:
        xs = corners[:, 0]
        zs = corners[:, 1]
    return float(xs.min()), float(zs.min()), float(xs.max()), float(zs.max())


def footprint_quality_from_boxes(bbox_scene, obj_class_ids, obj_sizes, dataset, translation_bounds):
    cls_dim = dataset.n_object_types + 1
    lower, upper = translation_bounds
    aabbs = []
    valid_indices = []
    out_of_bounds_centers = 0
    total_area = 0.0

    for idx, class_id in enumerate(obj_class_ids):
        if class_id == dataset.n_object_types:
            continue
        translation = np.asarray(bbox_scene[idx, cls_dim:cls_dim + 3], dtype=np.float32)
        angle = bbox_scene[idx, cls_dim + 6]
        size = np.asarray(obj_sizes[idx], dtype=np.float32)
        if translation[0] < lower[0] or translation[0] > upper[0] or translation[2] < lower[2] or translation[2] > upper[2]:
            out_of_bounds_centers += 1
        x0, z0, x1, z1 = footprint_aabb_from_trs(translation, angle, size)
        area = max(0.0, x1 - x0) * max(0.0, z1 - z0)
        total_area += area
        aabbs.append((x0, z0, x1, z1))
        valid_indices.append(idx)

    overlap_area = 0.0
    overlap_pairs = 0
    for i in range(len(aabbs)):
        x0, z0, x1, z1 = aabbs[i]
        for j in range(i + 1, len(aabbs)):
            ox0, oz0, ox1, oz1 = aabbs[j]
            iw = max(0.0, min(x1, ox1) - max(x0, ox0))
            ih = max(0.0, min(z1, oz1) - max(z0, oz0))
            area = iw * ih
            if area > 1e-4:
                overlap_pairs += 1
                overlap_area += area

    return {
        "object_count": int(len(valid_indices)),
        "out_of_bounds_centers": int(out_of_bounds_centers),
        "overlap_pairs": int(overlap_pairs),
        "overlap_area": float(overlap_area),
        "footprint_area": float(total_area),
        "overlap_ratio": float(overlap_area / max(total_area, 1e-8)),
    }


def serializable_boxes(bbox_scene, obj_class_ids, obj_sizes, dataset):
    cls_dim = dataset.n_object_types + 1
    records = []
    for idx, class_id in enumerate(obj_class_ids):
        if class_id == dataset.n_object_types:
            continue
        records.append({
            "index": int(idx),
            "class_id": int(class_id),
            "class_name": dataset.object_types[int(class_id)],
            "translation": [float(x) for x in bbox_scene[idx, cls_dim:cls_dim + 3]],
            "size": [float(x) for x in obj_sizes[idx]],
            "angle": float(bbox_scene[idx, cls_dim + 6]),
        })
    return records


def relation_base_name(name):
    return name.replace("closely ", "")


def canonical_predicate_phrase(phrase):
    phrase = re.sub(r"\s+", " ", phrase.lower().strip())
    phrase = phrase.replace("to the ", "")
    phrase = phrase.replace("close ", "closely ")
    phrase = phrase.replace("near ", "closely ")
    phrase = phrase.replace("closely closely ", "closely ")
    phrase = phrase.replace("closely left of", "closely left of")
    phrase = phrase.replace("closely right of", "closely right of")
    phrase = phrase.replace("closely in front of", "closely in front of")
    phrase = phrase.replace("closely behind", "closely behind")
    return phrase


def build_object_aliases(object_types):
    aliases = []
    for class_id, object_type in enumerate(object_types):
        name = object_type.replace("_", " ").lower()
        variants = {name}
        if name == "corner side table":
            variants.add("corner/side table")
            variants.add("corner table")
            variants.add("side table")
        if name == "bookshelf":
            variants.add("bookcase")
        if name == "multi-seat sofa":
            variants.add("three-seat sofa")
            variants.add("sofa")
        if name == "double bed":
            variants.add("king-size bed")
            variants.add("bed")
        if name == "single bed":
            variants.add("bed")
        for variant in variants:
            aliases.append((variant, class_id))
    aliases.sort(key=lambda x: len(x[0]), reverse=True)
    return aliases


def match_object_class(text, aliases):
    text = re.sub(r"[^a-z0-9\- ]+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    for alias, class_id in aliases:
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            return class_id
    return None


def split_instruction_sentences(text):
    parts = re.split(r"\.|;", text)
    sentences = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        part = re.sub(r"^(then|next|additionally|finnally|finally|and)\s*,?\s+", "", part, flags=re.I)
        sentences.append(part)
    return sentences


def parse_instruction_relations(text, object_types, predicate_types):
    aliases = build_object_aliases(object_types)
    predicate_patterns = [
        ("closely in front of", [r"closely\s+in\s+front\s+of"]),
        ("closely behind", [r"closely\s+behind"]),
        ("closely left of", [r"closely\s+left\s+of", r"closely\s+to\s+the\s+left\s+of", r"to\s+the\s+(?:close|near)\s+left\s+of"]),
        ("closely right of", [r"closely\s+right\s+of", r"closely\s+to\s+the\s+right\s+of", r"to\s+the\s+(?:close|near)\s+right\s+of"]),
        ("in front of", [r"in\s+front\s+of"]),
        ("behind", [r"behind"]),
        ("left of", [r"to\s+the\s+left\s+of", r"left\s+of"]),
        ("right of", [r"to\s+the\s+right\s+of", r"right\s+of"]),
        ("above", [r"above"]),
        ("below", [r"below"]),
    ]
    relations = []
    for sentence in split_instruction_sentences(text):
        lower = sentence.lower()
        best = None
        for predicate, patterns in predicate_patterns:
            for pattern in patterns:
                match = re.search(pattern, lower)
                if match is not None:
                    if best is None or match.start() < best[0].start():
                        best = (match, predicate)
        if best is None:
            continue
        match, predicate = best
        subject_text = sentence[:match.start()]
        object_text = sentence[match.end():]
        subject_text = re.sub(r"^(place|put|position|arrange|add|set up|hang|install)\s+", "", subject_text.strip(), flags=re.I)
        subj_cls = match_object_class(subject_text, aliases)
        obj_cls = match_object_class(object_text, aliases)
        if subj_cls is None or obj_cls is None:
            continue
        if predicate not in predicate_types:
            continue
        relations.append((int(subj_cls), int(predicate_types.index(predicate)), int(obj_cls)))
    return relations


def relation_target_offset(predicate_name, close_distance, far_distance):
    close = predicate_name.startswith("closely ")
    base = relation_base_name(predicate_name)
    dist = close_distance if close else far_distance
    if base == "right of":
        return np.array([dist, 0.0, 0.05], dtype=np.float32)
    if base == "left of":
        return np.array([-dist, 0.0, 0.05], dtype=np.float32)
    if base == "in front of":
        return np.array([0.05, 0.0, dist], dtype=np.float32)
    if base == "behind":
        return np.array([0.05, 0.0, -dist], dtype=np.float32)
    return None


def choose_pair_for_relation(obj_class_ids, subj_cls, obj_cls, bbox_scene, cls_dim):
    subj_idxs = [idx for idx, cls in enumerate(obj_class_ids) if cls == subj_cls]
    obj_idxs = [idx for idx, cls in enumerate(obj_class_ids) if cls == obj_cls]
    best = None
    best_dist = float("inf")
    for si in subj_idxs:
        for oi in obj_idxs:
            if si == oi:
                continue
            subj_t = bbox_scene[si, cls_dim:cls_dim + 3]
            obj_t = bbox_scene[oi, cls_dim:cls_dim + 3]
            d = np.linalg.norm(subj_t[[0, 2]] - obj_t[[0, 2]])
            if d < best_dist:
                best = (si, oi)
                best_dist = d
    return best


def clamp_pair_translation(subject_t, object_t, offset, lower, upper):
    desired_subject = subject_t.copy()
    desired_subject[[0, 2]] = object_t[[0, 2]] + offset[[0, 2]]
    shift = np.zeros(3, dtype=np.float32)
    for axis in (0, 2):
        if desired_subject[axis] < lower[axis]:
            shift[axis] = lower[axis] - desired_subject[axis]
        elif desired_subject[axis] > upper[axis]:
            shift[axis] = upper[axis] - desired_subject[axis]
    object_new = object_t.copy()
    subject_new = subject_t.copy()
    object_new[[0, 2]] = object_t[[0, 2]] + shift[[0, 2]]
    subject_new[[0, 2]] = object_new[[0, 2]] + offset[[0, 2]]
    for axis in (0, 2):
        object_new[axis] = np.minimum(np.maximum(object_new[axis], lower[axis]), upper[axis])
        subject_new[axis] = np.minimum(np.maximum(subject_new[axis], lower[axis]), upper[axis])
    return subject_new, object_new


def repair_candidate_score(candidate, old_subject, old_object, si, oi, obj_class_ids, obj_sizes, dataset, translation_bounds, overlap_weight):
    cls_dim = dataset.n_object_types + 1
    subject_t = candidate[si, cls_dim:cls_dim + 3]
    object_t = candidate[oi, cls_dim:cls_dim + 3]
    movement = float(
        np.linalg.norm(subject_t[[0, 2]] - old_subject[[0, 2]])
        + np.linalg.norm(object_t[[0, 2]] - old_object[[0, 2]])
    )
    quality = footprint_quality_from_boxes(candidate, obj_class_ids, obj_sizes, dataset, translation_bounds)
    return movement + overlap_weight * float(quality["overlap_area"]), movement


def choose_scene_prior_candidate(repaired, rel, si, oi, subject_new, object_new, old_subject, old_object, obj_class_ids, obj_sizes, dataset, translation_bounds, max_move, overlap_weight):
    cls_dim = dataset.n_object_types + 1
    best = None
    best_score = float("inf")
    for alpha in (0.25, 0.5, 0.75, 1.0):
        candidate = repaired.copy()
        cand_subject = old_subject.copy()
        cand_object = old_object.copy()
        cand_subject[[0, 2]] = old_subject[[0, 2]] + alpha * (subject_new[[0, 2]] - old_subject[[0, 2]])
        cand_object[[0, 2]] = old_object[[0, 2]] + alpha * (object_new[[0, 2]] - old_object[[0, 2]])
        candidate[si, cls_dim:cls_dim + 3] = cand_subject
        candidate[oi, cls_dim:cls_dim + 3] = cand_object
        current = layout_relations_from_boxes(candidate, obj_class_ids, obj_sizes, dataset)
        if rel not in current:
            continue
        score, movement = repair_candidate_score(
            candidate,
            old_subject,
            old_object,
            si,
            oi,
            obj_class_ids,
            obj_sizes,
            dataset,
            translation_bounds,
            overlap_weight,
        )
        if max_move > 0 and movement > max_move:
            continue
        if score < best_score:
            best_score = score
            best = candidate
    return best


def repair_layout_relations(bbox_scene, obj_class_ids, obj_sizes, selected_relations, dataset, translation_bounds, passes, close_distance, far_distance, strategy="direct", max_move=0.0, overlap_weight=0.0):
    repaired = bbox_scene.copy()
    cls_dim = dataset.n_object_types + 1
    lower, upper = translation_bounds
    edits = 0
    total_movement = 0.0
    skipped = 0

    for _ in range(passes):
        current = layout_relations_from_boxes(repaired, obj_class_ids, obj_sizes, dataset)
        for rel in selected_relations:
            rel = tuple(map(int, rel))
            if rel in current:
                continue
            subj_cls, pred_id, obj_cls = rel
            predicate_name = dataset.predicate_types[pred_id]
            offset = relation_target_offset(predicate_name, close_distance, far_distance)
            pair = choose_pair_for_relation(obj_class_ids, subj_cls, obj_cls, repaired, cls_dim)
            if pair is None or offset is None:
                skipped += 1
                continue
            si, oi = pair
            old_subject = repaired[si, cls_dim:cls_dim + 3].copy()
            old_object = repaired[oi, cls_dim:cls_dim + 3].copy()
            subject_new, object_new = clamp_pair_translation(old_subject, old_object, offset, lower, upper)
            if strategy == "floor_prior":
                candidate = choose_scene_prior_candidate(
                    repaired,
                    rel,
                    si,
                    oi,
                    subject_new,
                    object_new,
                    old_subject,
                    old_object,
                    obj_class_ids,
                    obj_sizes,
                    dataset,
                    translation_bounds,
                    max_move,
                    overlap_weight,
                )
                if candidate is None:
                    skipped += 1
                    continue
                subject_new = candidate[si, cls_dim:cls_dim + 3].copy()
                object_new = candidate[oi, cls_dim:cls_dim + 3].copy()
                repaired = candidate
            else:
                if max_move > 0:
                    movement = float(
                        np.linalg.norm(subject_new[[0, 2]] - old_subject[[0, 2]])
                        + np.linalg.norm(object_new[[0, 2]] - old_object[[0, 2]])
                    )
                    if movement > max_move:
                        skipped += 1
                        continue
                repaired[si, cls_dim:cls_dim + 3] = subject_new
                repaired[oi, cls_dim:cls_dim + 3] = object_new
            edits += 1
            total_movement += float(
                np.linalg.norm(subject_new[[0, 2]] - old_subject[[0, 2]])
                + np.linalg.norm(object_new[[0, 2]] - old_object[[0, 2]])
            )
    return repaired, {"edits": edits, "skipped": skipped, "total_movement": total_movement}


def add_counts(metrics, prefix, target_relations, predicted_relations, predicate_types):
    exact, easy = count_matches(target_relations, predicted_relations, predicate_types)
    metrics[prefix + "_correct"] += exact
    metrics[prefix + "_easy_correct"] += easy


def mesh_collision_quality(meshes):
    valid_meshes = [m for m in meshes if m is not None and len(m.faces) > 0 and len(m.vertices) > 0]
    total_pairs = len(valid_meshes) * (len(valid_meshes) - 1) // 2
    if total_pairs == 0:
        return {
            "available": True,
            "objects": len(valid_meshes),
            "total_pairs": 0,
            "collision_pairs": 0,
            "has_collision": False,
        }
    try:
        manager = trimesh.collision.CollisionManager()
        for idx, mesh in enumerate(valid_meshes):
            manager.add_object(str(idx), mesh)
        has_collision, names = manager.in_collision_internal(return_names=True)
    except BaseException as exc:
        return {
            "available": False,
            "objects": len(valid_meshes),
            "total_pairs": total_pairs,
            "collision_pairs": 0,
            "has_collision": False,
            "error": str(exc),
        }
    return {
        "available": True,
        "objects": len(valid_meshes),
        "total_pairs": total_pairs,
        "collision_pairs": len(names),
        "has_collision": bool(has_collision),
    }


def render_topdown_meshes(meshes, obj_classes, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    colors = [
        "#4e79a7", "#59a14f", "#f28e2b", "#e15759", "#76b7b2",
        "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    ]
    fig, ax = plt.subplots(figsize=(5.2, 5.2), dpi=150)
    all_x = []
    all_z = []
    for idx, mesh in enumerate(meshes):
        if mesh is None or len(mesh.faces) == 0:
            continue
        faces = mesh.faces
        if len(faces) > 900:
            step = max(len(faces) // 900, 1)
            faces = faces[::step]
        verts = mesh.vertices
        polys = [verts[face][:, [0, 2]] for face in faces]
        color = colors[idx % len(colors)]
        collection = PolyCollection(
            polys,
            facecolors=color,
            edgecolors="#202421",
            linewidths=0.08,
            alpha=0.58,
        )
        ax.add_collection(collection)
        all_x.extend(verts[:, 0].tolist())
        all_z.extend(verts[:, 2].tolist())
    if all_x and all_z:
        ax.set_xlim(min(all_x) - 0.35, max(all_x) + 0.35)
        ax.set_ylim(min(all_z) - 0.35, max(all_z) + 0.35)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("x")
    ax.set_ylabel("z")
    ax.grid(True, linewidth=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Relation-aware InstructScene evaluation")
    parser.add_argument("config_file", type=str)
    parser.add_argument("--tag", type=str, required=True)
    parser.add_argument("--fvqvae_tag", type=str, required=True)
    parser.add_argument("--fvqvae_epoch", type=int, default=1999)
    parser.add_argument("--sg2sc_tag", type=str, required=True)
    parser.add_argument("--sg2sc_epoch", type=int, default=1999)
    parser.add_argument("--output_dir", type=str, default="out")
    parser.add_argument("--checkpoint_epoch", type=int, default=None)
    parser.add_argument("--n_workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n_epochs", type=int, default=1)
    parser.add_argument("--n_scenes", type=int, default=5)
    parser.add_argument("--condition_type", type=str, default="text", choices=["text", "none"])
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--cfg_scale", type=float, default=1.0)
    parser.add_argument("--sg2sc_cfg_scale", type=float, default=1.0)
    parser.add_argument("--relation_source", type=str, default="oracle", choices=["oracle", "parsed"])
    parser.add_argument("--repair_passes", type=int, default=2)
    parser.add_argument("--close_distance", type=float, default=0.75)
    parser.add_argument("--far_distance", type=float, default=1.6)
    parser.add_argument("--repair_strategy", type=str, default="direct", choices=["direct", "floor_prior"])
    parser.add_argument("--max_repair_move", type=float, default=0.0)
    parser.add_argument("--repair_overlap_weight", type=float, default=1.0)
    parser.add_argument("--output_suffix", type=str, default="")
    parser.add_argument("--mesh_collision", action="store_true")
    parser.add_argument("--render_examples", type=int, default=0)
    parser.add_argument(
        "--skip_object_matching",
        action="store_true",
        help="Evaluate generated layouts without matching boxes to textured 3D-FUTURE objects.",
    )
    args = parser.parse_args()

    if args.seed is not None and args.seed >= 0:
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(args.seed)
        print(f"You have chosen to seed([{args.seed}]) the experiment")

    device = torch.device(f"cuda:{args.device}" if torch.cuda.is_available() else "cpu")
    print(f"Run code on device [{device}]\n")

    exp_dir = os.path.join(args.output_dir, args.tag)
    ckpt_dir = os.path.join(exp_dir, "checkpoints")
    assert os.path.exists(ckpt_dir), f"Checkpoint directory {ckpt_dir} does not exist"
    config = load_config(args.config_file)

    objects_dataset = ThreedFutureDataset.from_pickled_dataset(config["data"]["path_to_pickled_3d_futute_models"])
    print(f"Load [{len(objects_dataset)}] 3D-FUTURE models")

    if not os.path.exists(os.path.join(exp_dir, "bounds.npz")):
        train_dataset = get_encoded_dataset(
            config["data"],
            filter_function(config["data"], split=config["training"].get("splits", ["train", "val"])),
            path_to_bounds=None,
            augmentations=None,
            split=config["training"].get("splits", ["train", "val"]),
        )
        np.savez(
            os.path.join(exp_dir, "bounds.npz"),
            translations=train_dataset.bounds["translations"],
            sizes=train_dataset.bounds["sizes"],
            angles=train_dataset.bounds["angles"],
        )
        print(f"Training set has bounds: {train_dataset.bounds}")

    config["data"]["encoding_type"] += "_sincos_angle"
    if "eval" not in config["data"]["encoding_type"]:
        config["data"]["encoding_type"] += "_eval"
    _raw_dataset, dataset = get_dataset_raw_and_encoded(
        config["data"],
        filter_fn=filter_function(config["data"], split=config["validation"].get("splits", ["test"])),
        path_to_bounds=os.path.join(exp_dir, "bounds.npz"),
        augmentations=None,
        split=config["validation"].get("splits", ["test"]),
    )
    print(f"Load [{len(dataset)}] validation scenes with [{dataset.n_object_types}] object types\n")

    B = config["validation"]["batch_size"] if args.n_scenes == 0 else args.n_scenes
    dataloader = DataLoader(
        dataset,
        batch_size=B,
        num_workers=args.n_workers,
        pin_memory=False,
        collate_fn=dataset.collate_fn,
        shuffle=False,
    )

    print(f"Load pretrained text encoder [{config['model']['text_encoder']}]\n")
    if "clip" in config["model"]["text_encoder"]:
        text_encoder = CLIPTextEncoder(config["model"]["text_encoder"], device=device)
    else:
        raise ValueError(f"Invalid text encoder name: [{config['model']['text_encoder']}]")

    print("Load pretrained VQ-VAE\n")
    with open(f"{args.output_dir}/{args.fvqvae_tag}/objfeat_bounds.pkl", "rb") as f:
        kwargs = pickle.load(f)
    vqvae_model = ObjectFeatureVQVAE("openshape_vitg14", "gumbel", **kwargs)
    ckpt_path = f"{args.output_dir}/{args.fvqvae_tag}/checkpoints/epoch_{args.fvqvae_epoch:05d}.pth"
    vqvae_model.load_state_dict(torch.load(ckpt_path, map_location="cpu")["model"])
    vqvae_model = vqvae_model.to(device)
    vqvae_model.eval()

    model = model_from_config(
        config["model"],
        dataset.n_object_types,
        dataset.n_predicate_types,
        text_emb_dim=text_encoder.text_emb_dim,
    ).to(device)
    ema_config = config["training"]["ema"]
    ema_states = EMAModel(model.parameters()) if ema_config["use_ema"] else None
    if ema_states is not None:
        ema_states.to(device)
    load_epoch = load_checkpoints(model, ckpt_dir, ema_states, epoch=args.checkpoint_epoch, device=device)
    if ema_states is not None:
        print("Copy EMA parameters to the model\n")
        ema_states.copy_to(model.parameters())
    model.eval()

    sg2sc_model = Sg2ScDiffusion(
        dataset.n_object_types,
        dataset.n_predicate_types,
        use_objfeat="objfeat" in config["model"]["name"],
    ).to(device)
    sg2sc_ema_states = EMAModel(sg2sc_model.parameters()) if ema_config["use_ema"] else None
    if sg2sc_ema_states is not None:
        sg2sc_ema_states.to(device)
    load_checkpoints(
        sg2sc_model,
        f"{args.output_dir}/{args.sg2sc_tag}/checkpoints",
        sg2sc_ema_states,
        epoch=args.sg2sc_epoch,
        device=device,
    )
    if sg2sc_ema_states is not None:
        print("Copy EMA parameters to the sg2sc model\n")
        sg2sc_ema_states.copy_to(sg2sc_model.parameters())
    sg2sc_model.eval()

    save_dir = os.path.join(exp_dir, "generated_scenes", f"epoch_{load_epoch:05d}")
    os.makedirs(save_dir, exist_ok=True)
    render_dir = os.path.join(save_dir, f"relation_aware_{args.relation_source}_renders")
    if args.render_examples > 0:
        os.makedirs(render_dir, exist_ok=True)
    rendered_examples = 0
    classes = np.array(dataset.object_types)
    bounds = np.load(os.path.join(exp_dir, "bounds.npz"))
    translation_bounds = (bounds["translations"][0], bounds["translations"][1])

    metrics = {
        "rel_total": 0,
        "graph_correct": 0,
        "graph_easy_correct": 0,
        "layout_correct": 0,
        "layout_easy_correct": 0,
        "repair_correct": 0,
        "repair_easy_correct": 0,
        "repair_edits": 0,
        "repair_skipped": 0,
        "repair_total_movement": 0.0,
        "parsed_total": 0,
        "parsed_oracle_exact": 0,
        "parsed_oracle_easy": 0,
        "object_count": 0,
        "layout_overlap_pairs": 0,
        "layout_overlap_area": 0.0,
        "layout_footprint_area": 0.0,
        "layout_out_of_bounds_centers": 0,
        "layout_scenes_with_overlap": 0,
        "repair_overlap_pairs": 0,
        "repair_overlap_area": 0.0,
        "repair_footprint_area": 0.0,
        "repair_out_of_bounds_centers": 0,
        "repair_scenes_with_overlap": 0,
        "mesh_collision_scenes_evaluated": 0,
        "layout_mesh_collision_pairs": 0,
        "layout_mesh_total_pairs": 0,
        "layout_mesh_collision_scenes": 0,
        "repair_mesh_collision_pairs": 0,
        "repair_mesh_total_pairs": 0,
        "repair_mesh_collision_scenes": 0,
    }
    per_scene = []

    print("Sample scene graphs with relation-aware post-hoc repair")
    for epoch in range(args.n_epochs):
        for batch_idx, batch in tqdm(
            enumerate(dataloader),
            desc=f"[{epoch:2d}/{args.n_epochs:2d}] Process each batch",
            total=len(dataloader),
            ncols=125,
            disable=args.verbose,
        ):
            descriptions = batch["descriptions"]
            texts = []
            batch_selected_relations = []
            for desc_idx, desc in enumerate(descriptions):
                text, selected_relations, _selected_descs = fill_templates(
                    desc,
                    dataset.object_types,
                    dataset.predicate_types,
                    batch["object_descs"][desc_idx],
                    seed=epoch * len(dataset) + batch_idx * B + desc_idx,
                )
                texts.append(text)
                batch_selected_relations.append(selected_relations)
            text_last_hidden_state, text_embeds = text_encoder(texts)
            if args.condition_type == "none":
                text_last_hidden_state = torch.zeros_like(text_last_hidden_state)
                text_embeds = torch.zeros_like(text_embeds)

            with torch.no_grad():
                bs, n = batch["objs"].shape[0], config["data"]["max_length"]
                objs, edges, objfeat_vq_indices = model.generate_samples(
                    bs,
                    n,
                    text_last_hidden_state,
                    text_embeds,
                    cfg_scale=args.cfg_scale,
                )
                if objfeat_vq_indices is not None:
                    rand_indices = torch.randint_like(objfeat_vq_indices, 0, 64)
                    objfeat_vq_indices[objfeat_vq_indices == 64] = rand_indices[objfeat_vq_indices == 64]

            objs = objs.argmax(dim=-1)
            obj_masks = (objs != dataset.n_object_types).long()
            edges = edges.argmax(dim=-1)
            edges = F.one_hot(edges, num_classes=dataset.n_predicate_types + 1).float()
            edges = scatter_trilist_to_matrix(edges, objs.shape[-1])
            e_mask1 = obj_masks.unsqueeze(1).unsqueeze(-1)
            e_mask2 = obj_masks.unsqueeze(2).unsqueeze(-1)
            edges = edges * e_mask1 * e_mask2
            edges_negative = edges[..., [*range(dataset.n_predicate_types // 2, dataset.n_predicate_types)] + [*range(0, dataset.n_predicate_types // 2)] + [*range(dataset.n_predicate_types, edges.shape[-1])]]
            edges = edges + edges_negative.permute(0, 2, 1, 3)
            edge_mask = torch.eye(objs.shape[-1], device=device).bool().unsqueeze(0).unsqueeze(-1)
            edge_mask = ((~edge_mask).float() * e_mask1 * e_mask2).squeeze(-1)
            edges_empty = edges[edges.sum(dim=-1) == 0]
            edges_empty[..., -1] = 1.0
            edges[edges.sum(dim=-1) == 0] = edges_empty
            edges = torch.argmax(edges, dim=-1)

            with torch.no_grad():
                boxes_pred = sg2sc_model.generate_samples(
                    objs,
                    edges,
                    objfeat_vq_indices,
                    obj_masks,
                    vqvae_model,
                    cfg_scale=args.sg2sc_cfg_scale,
                )

            if objfeat_vq_indices is not None:
                BB, N = objfeat_vq_indices.shape[:2]
                objfeats = vqvae_model.reconstruct_from_indices(objfeat_vq_indices.reshape(BB * N, -1)).reshape(BB, N, -1)
                objfeats = objfeats.cpu().numpy()
            else:
                objfeats = None

            objs_cpu = objs.cpu()
            edges_cpu = edges.cpu()
            boxes_pred = boxes_pred.cpu()
            bbox_params = {
                "class_labels": F.one_hot(objs_cpu, num_classes=dataset.n_object_types + 1).float(),
                "translations": boxes_pred[..., :3],
                "sizes": boxes_pred[..., 3:6],
                "angles": boxes_pred[..., 6:],
            }
            boxes = dataset.post_process(bbox_params)
            bbox_params_t = torch.cat([
                boxes["class_labels"],
                boxes["translations"],
                boxes["sizes"],
                boxes["angles"],
            ], dim=-1).numpy()

            progress_bar = tqdm(
                total=len(bbox_params_t),
                desc="Evaluate scenes",
                ncols=125,
                disable=args.verbose,
            )
            for i in range(len(bbox_params_t)):
                if args.skip_object_matching:
                    class_ids = bbox_params_t[i, :, :dataset.n_object_types + 1].argmax(axis=-1)
                    obj_class_ids = [
                        int(c) if int(c) < dataset.n_object_types else dataset.n_object_types
                        for c in class_ids
                    ]
                    obj_classes = [
                        dataset.object_types[c] if c < dataset.n_object_types else None
                        for c in obj_class_ids
                    ]
                    obj_sizes = bbox_params_t[i, :, dataset.n_object_types + 4:dataset.n_object_types + 7]
                    _trimesh_meshes = []
                    _obj_ids = [None] * len(obj_class_ids)
                else:
                    _trimesh_meshes, _bbox_meshes, obj_classes, obj_sizes, _obj_ids = get_textured_objects(
                        bbox_params_t[i],
                        objects_dataset,
                        classes,
                        objfeats[i] if objfeats is not None else None,
                        "openshape_vitg14",
                        verbose=args.verbose,
                    )
                    obj_class_ids = [
                        dataset.object_types.index(c) if c is not None else dataset.n_object_types
                        for c in obj_classes
                    ]
                selected = [tuple(map(int, rel)) for rel in batch_selected_relations[i]]
                parsed = parse_instruction_relations(texts[i], dataset.object_types, dataset.predicate_types)
                repair_targets = selected if args.relation_source == "oracle" else parsed
                if len(selected) == 0:
                    progress_bar.update(1)
                    continue

                metrics["parsed_total"] += len(parsed)
                parser_exact, parser_easy = count_matches(selected, parsed, dataset.predicate_types)
                metrics["parsed_oracle_exact"] += parser_exact
                metrics["parsed_oracle_easy"] += parser_easy

                graph_rels = graph_relations_from_edges(edges_cpu[i], obj_class_ids, dataset.n_object_types, dataset.n_predicate_types)
                layout_rels = layout_relations_from_boxes(bbox_params_t[i], obj_class_ids, obj_sizes, dataset)
                repaired_box, repair_stats = repair_layout_relations(
                    bbox_params_t[i],
                    obj_class_ids,
                    obj_sizes,
                    repair_targets,
                    dataset,
                    translation_bounds,
                    args.repair_passes,
                    args.close_distance,
                    args.far_distance,
                    args.repair_strategy,
                    args.max_repair_move,
                    args.repair_overlap_weight,
                )
                repair_rels = layout_relations_from_boxes(repaired_box, obj_class_ids, obj_sizes, dataset)
                layout_quality = footprint_quality_from_boxes(
                    bbox_params_t[i],
                    obj_class_ids,
                    obj_sizes,
                    dataset,
                    translation_bounds,
                )
                repair_quality = footprint_quality_from_boxes(
                    repaired_box,
                    obj_class_ids,
                    obj_sizes,
                    dataset,
                    translation_bounds,
                )
                layout_mesh_quality = None
                repair_mesh_quality = None
                repair_obj_ids = None
                repair_meshes = None
                if args.mesh_collision or args.render_examples > 0:
                    repair_meshes, _repair_bbox_meshes, _repair_obj_classes, _repair_obj_sizes, repair_obj_ids = get_textured_objects(
                        repaired_box,
                        objects_dataset,
                        classes,
                        objfeats[i] if objfeats is not None else None,
                        "openshape_vitg14",
                        verbose=args.verbose,
                    )
                if args.mesh_collision:
                    layout_mesh_quality = mesh_collision_quality(_trimesh_meshes)
                    repair_mesh_quality = mesh_collision_quality(repair_meshes)
                    if layout_mesh_quality.get("available") and repair_mesh_quality.get("available"):
                        metrics["mesh_collision_scenes_evaluated"] += 1
                        metrics["layout_mesh_collision_pairs"] += layout_mesh_quality["collision_pairs"]
                        metrics["layout_mesh_total_pairs"] += layout_mesh_quality["total_pairs"]
                        metrics["layout_mesh_collision_scenes"] += int(layout_mesh_quality["has_collision"])
                        metrics["repair_mesh_collision_pairs"] += repair_mesh_quality["collision_pairs"]
                        metrics["repair_mesh_total_pairs"] += repair_mesh_quality["total_pairs"]
                        metrics["repair_mesh_collision_scenes"] += int(repair_mesh_quality["has_collision"])

                rel_n = len(selected)
                metrics["rel_total"] += rel_n
                add_counts(metrics, "graph", selected, graph_rels, dataset.predicate_types)
                add_counts(metrics, "layout", selected, layout_rels, dataset.predicate_types)
                add_counts(metrics, "repair", selected, repair_rels, dataset.predicate_types)
                metrics["repair_edits"] += repair_stats["edits"]
                metrics["repair_skipped"] += repair_stats["skipped"]
                metrics["repair_total_movement"] += repair_stats["total_movement"]
                metrics["object_count"] += layout_quality["object_count"]
                metrics["layout_overlap_pairs"] += layout_quality["overlap_pairs"]
                metrics["layout_overlap_area"] += layout_quality["overlap_area"]
                metrics["layout_footprint_area"] += layout_quality["footprint_area"]
                metrics["layout_out_of_bounds_centers"] += layout_quality["out_of_bounds_centers"]
                metrics["layout_scenes_with_overlap"] += int(layout_quality["overlap_pairs"] > 0)
                metrics["repair_overlap_pairs"] += repair_quality["overlap_pairs"]
                metrics["repair_overlap_area"] += repair_quality["overlap_area"]
                metrics["repair_footprint_area"] += repair_quality["footprint_area"]
                metrics["repair_out_of_bounds_centers"] += repair_quality["out_of_bounds_centers"]
                metrics["repair_scenes_with_overlap"] += int(repair_quality["overlap_pairs"] > 0)

                layout_exact, _layout_easy = count_matches(selected, layout_rels, dataset.predicate_types)
                repair_exact, _repair_easy = count_matches(selected, repair_rels, dataset.predicate_types)
                render_paths = {}
                if (
                    args.render_examples > 0
                    and rendered_examples < args.render_examples
                    and repair_exact > layout_exact
                    and repair_meshes is not None
                ):
                    stem = f"scene_{len(per_scene):04d}_{batch['scene_uids'][i]}"
                    before_path = os.path.join(render_dir, f"{stem}_before.png")
                    after_path = os.path.join(render_dir, f"{stem}_after.png")
                    render_topdown_meshes(_trimesh_meshes, obj_classes, before_path, f"Before {layout_exact}/{rel_n}")
                    render_topdown_meshes(repair_meshes, obj_classes, after_path, f"After {repair_exact}/{rel_n}")
                    render_paths = {
                        "before": before_path,
                        "after": after_path,
                    }
                    rendered_examples += 1

                scene_record = {
                    "scene_uid": str(batch["scene_uids"][i]),
                    "text": texts[i],
                    "selected_relations": [[int(x) for x in rel] for rel in selected],
                    "parsed_relations": [[int(x) for x in rel] for rel in parsed],
                    "repair_target_relations": [[int(x) for x in rel] for rel in repair_targets],
                    "graph_relations": [[int(x) for x in rel] for rel in graph_rels],
                    "layout_relations": [[int(x) for x in rel] for rel in layout_rels],
                    "repair_relations": [[int(x) for x in rel] for rel in repair_rels],
                    "repair_stats": repair_stats,
                    "layout_quality": layout_quality,
                    "repair_quality": repair_quality,
                    "layout_mesh_collision": layout_mesh_quality,
                    "repair_mesh_collision": repair_mesh_quality,
                    "object_model_jids": [None if x is None else str(x) for x in _obj_ids],
                    "repair_object_model_jids": None if repair_obj_ids is None else [None if x is None else str(x) for x in repair_obj_ids],
                    "render_paths": render_paths,
                    "layout_boxes": serializable_boxes(bbox_params_t[i], obj_class_ids, obj_sizes, dataset),
                    "repair_boxes": serializable_boxes(repaired_box, obj_class_ids, obj_sizes, dataset),
                }
                per_scene.append(scene_record)

                progress_bar.update(1)
                progress_bar.set_postfix({
                    "base": f"{metrics['layout_correct'] / max(metrics['rel_total'], 1):.4f}",
                    "repair": f"{metrics['repair_correct'] / max(metrics['rel_total'], 1):.4f}",
                })

            if args.n_scenes != 0:
                break

    rel_total = max(metrics["rel_total"], 1)
    result = {
        "args": vars(args),
        "metrics": metrics,
        "scores": {
            "graph_relation_acc": metrics["graph_correct"] / rel_total,
            "graph_relation_acc_easy": metrics["graph_easy_correct"] / rel_total,
            "baseline_relation_acc": metrics["layout_correct"] / rel_total,
            "baseline_relation_acc_easy": metrics["layout_easy_correct"] / rel_total,
            "repaired_relation_acc": metrics["repair_correct"] / rel_total,
            "repaired_relation_acc_easy": metrics["repair_easy_correct"] / rel_total,
            "avg_repair_movement": metrics["repair_total_movement"] / max(metrics["repair_edits"], 1),
            "parser_relation_precision": metrics["parsed_oracle_exact"] / max(metrics["parsed_total"], 1),
            "parser_relation_recall": metrics["parsed_oracle_exact"] / rel_total,
            "parser_relation_recall_easy": metrics["parsed_oracle_easy"] / rel_total,
            "layout_overlap_ratio": metrics["layout_overlap_area"] / max(metrics["layout_footprint_area"], 1e-8),
            "repair_overlap_ratio": metrics["repair_overlap_area"] / max(metrics["repair_footprint_area"], 1e-8),
            "layout_overlap_pairs_per_scene": metrics["layout_overlap_pairs"] / max(len(per_scene), 1),
            "repair_overlap_pairs_per_scene": metrics["repair_overlap_pairs"] / max(len(per_scene), 1),
            "layout_out_of_bounds_rate": metrics["layout_out_of_bounds_centers"] / max(metrics["object_count"], 1),
            "repair_out_of_bounds_rate": metrics["repair_out_of_bounds_centers"] / max(metrics["object_count"], 1),
            "mesh_collision_scenes_evaluated": metrics["mesh_collision_scenes_evaluated"],
            "layout_mesh_collision_pair_rate": metrics["layout_mesh_collision_pairs"] / max(metrics["layout_mesh_total_pairs"], 1),
            "repair_mesh_collision_pair_rate": metrics["repair_mesh_collision_pairs"] / max(metrics["repair_mesh_total_pairs"], 1),
            "layout_mesh_collision_scene_rate": metrics["layout_mesh_collision_scenes"] / max(metrics["mesh_collision_scenes_evaluated"], 1),
            "repair_mesh_collision_scene_rate": metrics["repair_mesh_collision_scenes"] / max(metrics["mesh_collision_scenes_evaluated"], 1),
        },
        "per_scene": per_scene,
    }

    suffix = args.output_suffix.strip()
    if not suffix:
        suffix = f"{args.repair_strategy}_p{args.repair_passes}_close{args.close_distance}_far{args.far_distance}"
        if args.max_repair_move > 0:
            suffix += f"_maxmove{args.max_repair_move}"
        if args.mesh_collision:
            suffix += "_mesh"
    txt_path = os.path.join(save_dir, f"relation_aware_{args.relation_source}_{suffix}_eval_cfg{args.cfg_scale:.1f}_{args.sg2sc_cfg_scale:.1f}.txt")
    json_path = os.path.join(save_dir, f"relation_aware_{args.relation_source}_{suffix}_eval_cfg{args.cfg_scale:.1f}_{args.sg2sc_cfg_scale:.1f}.json")
    lines = [
        f"Repair strategy: {args.repair_strategy}",
        f"Max repair move: {args.max_repair_move:.4f}",
        f"Repair overlap weight: {args.repair_overlap_weight:.4f}",
        f"Graph relation acc: [{metrics['graph_correct']:4d}/{metrics['rel_total']:4d}] = {result['scores']['graph_relation_acc']:.4f}",
        f"Graph relation acc (easy): [{metrics['graph_easy_correct']:4d}/{metrics['rel_total']:4d}] = {result['scores']['graph_relation_acc_easy']:.4f}",
        f"Baseline relation acc: [{metrics['layout_correct']:4d}/{metrics['rel_total']:4d}] = {result['scores']['baseline_relation_acc']:.4f}",
        f"Baseline relation acc (easy): [{metrics['layout_easy_correct']:4d}/{metrics['rel_total']:4d}] = {result['scores']['baseline_relation_acc_easy']:.4f}",
        f"Relation-aware repaired acc: [{metrics['repair_correct']:4d}/{metrics['rel_total']:4d}] = {result['scores']['repaired_relation_acc']:.4f}",
        f"Relation-aware repaired acc (easy): [{metrics['repair_easy_correct']:4d}/{metrics['rel_total']:4d}] = {result['scores']['repaired_relation_acc_easy']:.4f}",
        f"Repair edits: {metrics['repair_edits']}",
        f"Repair skipped: {metrics['repair_skipped']}",
        f"Average repair movement: {result['scores']['avg_repair_movement']:.4f}",
        f"Relation source: {args.relation_source}",
        f"Parsed relations: {metrics['parsed_total']}",
        f"Parser exact recall: [{metrics['parsed_oracle_exact']:4d}/{metrics['rel_total']:4d}] = {result['scores']['parser_relation_recall']:.4f}",
        f"Parser easy recall: [{metrics['parsed_oracle_easy']:4d}/{metrics['rel_total']:4d}] = {result['scores']['parser_relation_recall_easy']:.4f}",
        f"Parser precision: {result['scores']['parser_relation_precision']:.4f}",
        f"Baseline footprint overlap ratio: {result['scores']['layout_overlap_ratio']:.6f}",
        f"Repaired footprint overlap ratio: {result['scores']['repair_overlap_ratio']:.6f}",
        f"Baseline overlap pairs/scene: {result['scores']['layout_overlap_pairs_per_scene']:.4f}",
        f"Repaired overlap pairs/scene: {result['scores']['repair_overlap_pairs_per_scene']:.4f}",
        f"Baseline out-of-bounds center rate: {result['scores']['layout_out_of_bounds_rate']:.6f}",
        f"Repaired out-of-bounds center rate: {result['scores']['repair_out_of_bounds_rate']:.6f}",
        f"Mesh collision scenes evaluated: {result['scores']['mesh_collision_scenes_evaluated']}",
        f"Baseline mesh collision pair rate: {result['scores']['layout_mesh_collision_pair_rate']:.6f}",
        f"Repaired mesh collision pair rate: {result['scores']['repair_mesh_collision_pair_rate']:.6f}",
        f"Baseline mesh collision scene rate: {result['scores']['layout_mesh_collision_scene_rate']:.6f}",
        f"Repaired mesh collision scene rate: {result['scores']['repair_mesh_collision_scene_rate']:.6f}",
    ]
    with open(txt_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print("\n".join(lines))
    print(f"Saved relation-aware results to {txt_path}")
    print(f"Saved per-scene details to {json_path}")


if __name__ == "__main__":
    main()
