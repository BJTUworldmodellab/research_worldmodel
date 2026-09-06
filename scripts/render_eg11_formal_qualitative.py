#!/usr/bin/env python3
"""Render deterministic EG11 formal before/after layout evidence.

The renderer uses only the frozen EG07 layout artifact and the EG05 independent
per-relation evaluation.  It intentionally does not use historical showcase
renders or manually selected examples.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas


ROOMS = ("bedroom", "livingroom", "diningroom")
BASELINE = "baseline"
MAIN = "collision_gated_floor_prior"

COLORS = {
    "subject": "#2E6FBB",
    "object": "#E58B2A",
    "other": "#D6D9DE",
    "outline": "#252A34",
    "pass": "#17833B",
    "fail": "#B42318",
    "grid": "#E8EAED",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_layouts(path: Path) -> dict[tuple[str, str], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        (item["scene_id"], item["layout_variant"]): item
        for item in payload["layouts"]
    }


def moved(before: dict, after: dict) -> bool:
    before_by_index = {obj["index"]: obj for obj in before["objects"]}
    for obj in after["objects"]:
        old = before_by_index.get(obj["index"])
        if old is None:
            continue
        if math.hypot(
            float(obj["center"][0]) - float(old["center"][0]),
            float(obj["center"][2]) - float(old["center"][2]),
        ) > 1e-8:
            return True
    return False


def choose_examples(
    relation_rows: list[dict[str, str]],
    layouts: dict[tuple[str, str], dict],
) -> list[dict[str, object]]:
    rows = {
        (row["scene_id"], row["relation_id"], row["layout_variant"]): row
        for row in relation_rows
    }
    relation_keys = sorted({(row["scene_id"], row["relation_id"]) for row in relation_rows})

    successes: list[dict[str, object]] = []
    for room in ROOMS:
        selected = None
        for scene_id, relation_id in relation_keys:
            before_row = rows.get((scene_id, relation_id, BASELINE))
            after_row = rows.get((scene_id, relation_id, MAIN))
            before = layouts.get((scene_id, BASELINE))
            after = layouts.get((scene_id, MAIN))
            if not all((before_row, after_row, before, after)):
                continue
            if before_row["room_type"] != room:
                continue
            if before_row["status"] != "evaluated" or after_row["status"] != "evaluated":
                continue
            if before_row["is_satisfied"] != "0" or after_row["is_satisfied"] != "1":
                continue
            if not moved(before, after):
                continue
            selected = {
                "kind": "success",
                "room_type": room,
                "scene_id": scene_id,
                "relation_id": relation_id,
                "before_row": before_row,
                "after_row": after_row,
                "before": before,
                "after": after,
            }
            break
        if selected is None:
            raise RuntimeError(f"no deterministic success example found for {room}")
        successes.append(selected)

    failure = None
    for scene_id, relation_id in relation_keys:
        before_row = rows.get((scene_id, relation_id, BASELINE))
        after_row = rows.get((scene_id, relation_id, MAIN))
        before = layouts.get((scene_id, BASELINE))
        after = layouts.get((scene_id, MAIN))
        if not all((before_row, after_row, before, after)):
            continue
        if before_row["status"] != "evaluated" or after_row["status"] != "evaluated":
            continue
        if before_row["is_satisfied"] != "0" or after_row["is_satisfied"] != "0":
            continue
        if after.get("gate", {}).get("decision") != "repair" or not moved(before, after):
            continue
        failure = {
            "kind": "remaining_failure",
            "room_type": before_row["room_type"],
            "scene_id": scene_id,
            "relation_id": relation_id,
            "before_row": before_row,
            "after_row": after_row,
            "before": before,
            "after": after,
        }
        break
    if failure is None:
        raise RuntimeError("no deterministic remaining-failure example found")
    return [*successes, failure]


def bounds(example: dict[str, object]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    zs: list[float] = []
    for layout in (example["before"], example["after"]):
        for obj in layout["objects"]:
            x, z = float(obj["center"][0]), float(obj["center"][2])
            hx, hz = float(obj["size"][0]), float(obj["size"][2])
            radius = math.hypot(hx, hz)
            xs.extend((x - radius, x + radius))
            zs.extend((z - radius, z + radius))
    xmin, xmax = min(xs), max(xs)
    zmin, zmax = min(zs), max(zs)
    span = max(xmax - xmin, zmax - zmin, 1.0)
    margin = 0.08 * span
    return xmin - margin, xmax + margin, zmin - margin, zmax + margin


def panel_transform(
    bbox: tuple[float, float, float, float],
    panel: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    xmin, xmax, zmin, zmax = bbox
    x0, y0, width, height = panel
    scale = min(width / (xmax - xmin), height / (zmax - zmin))
    ox = x0 + (width - (xmax - xmin) * scale) / 2 - xmin * scale
    oy = y0 + (height - (zmax - zmin) * scale) / 2 - zmin * scale
    return scale, ox, oy


def object_role(obj_index: int, row: dict[str, str]) -> str:
    if obj_index == int(row["subject_index"]):
        return "subject"
    if obj_index == int(row["object_index"]):
        return "object"
    return "other"


def short_category(category: str) -> str:
    return category.replace("_", " ")[:18]


def draw_pdf_panel(
    pdf: canvas.Canvas,
    layout: dict,
    row: dict[str, str],
    bbox: tuple[float, float, float, float],
    panel: tuple[float, float, float, float],
    label: str,
) -> None:
    x0, y0, width, height = panel
    scale, ox, oy = panel_transform(bbox, panel)
    pdf.setFillColor(HexColor("#FAFBFC"))
    pdf.setStrokeColor(HexColor(COLORS["grid"]))
    pdf.rect(x0, y0, width, height, fill=1, stroke=1)
    pdf.setFont("Helvetica-Bold", 7)
    pdf.setFillColor(HexColor("#252A34"))
    pdf.drawString(x0 + 4, y0 + height - 10, label)

    for obj in layout["objects"]:
        role = object_role(int(obj["index"]), row)
        cx = ox + float(obj["center"][0]) * scale
        cy = oy + float(obj["center"][2]) * scale
        width_obj = max(2.0, 2 * float(obj["size"][0]) * scale)
        height_obj = max(2.0, 2 * float(obj["size"][2]) * scale)
        pdf.saveState()
        pdf.translate(cx, cy)
        pdf.rotate(math.degrees(float(obj.get("yaw", 0.0))))
        pdf.setFillColor(HexColor(COLORS[role]))
        pdf.setStrokeColor(HexColor(COLORS["outline"]))
        pdf.setLineWidth(0.55 if role != "other" else 0.3)
        pdf.rect(-width_obj / 2, -height_obj / 2, width_obj, height_obj, fill=1, stroke=1)
        pdf.restoreState()
        if role != "other":
            pdf.setFont("Helvetica", 5.7)
            pdf.setFillColor(black)
            pdf.drawCentredString(cx, cy - 2, short_category(obj["category"]))

    satisfied = row["is_satisfied"] == "1"
    pdf.setFont("Helvetica-Bold", 7)
    pdf.setFillColor(HexColor(COLORS["pass"] if satisfied else COLORS["fail"]))
    pdf.drawRightString(x0 + width - 4, y0 + height - 10, "PASS" if satisfied else "FAIL")


def render_pdf(path: Path, examples: list[dict[str, object]]) -> None:
    page = landscape((842, 360))
    pdf = canvas.Canvas(str(path), pagesize=page, pageCompression=1)
    page_width, page_height = page
    margin = 18
    gap = 9
    column_width = (page_width - 2 * margin - 3 * gap) / 4
    title_height = 42
    row_gap = 9
    panel_height = (page_height - title_height - margin - row_gap) / 2

    pdf.setFillColor(white)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(black)
    pdf.drawString(margin, page_height - 18, "Frozen EG07 formal layouts: deterministic before/after evidence")
    pdf.setFont("Helvetica", 7)
    pdf.drawString(
        margin,
        page_height - 31,
        "Blue = relation subject; orange = relation object; gray = other objects. Top: original layout. Bottom: collision-gated Floor-Prior.",
    )

    for col, example in enumerate(examples):
        x = margin + col * (column_width + gap)
        bbox = bounds(example)
        row = example["before_row"]
        relation_text = f"{row['subject_class']} {row['predicate']} {row['object_class']}"
        heading = (
            f"{example['room_type']} success" if example["kind"] == "success" else f"{example['room_type']} remaining failure"
        )
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.setFillColor(black)
        pdf.drawString(x, page_height - 43, heading)
        pdf.setFont("Helvetica", 6.3)
        pdf.drawString(x, page_height - 53, relation_text[:43])

        top_panel = (x, margin + panel_height + row_gap, column_width, panel_height)
        bottom_panel = (x, margin, column_width, panel_height)
        draw_pdf_panel(pdf, example["before"], example["before_row"], bbox, top_panel, "Original")
        draw_pdf_panel(pdf, example["after"], example["after_row"], bbox, bottom_panel, "Gated repair")

    pdf.showPage()
    pdf.save()


def rotate_point(x: float, y: float, angle: float) -> tuple[float, float]:
    c, s = math.cos(angle), math.sin(angle)
    return x * c - y * s, x * s + y * c


def render_png(path: Path, examples: list[dict[str, object]]) -> None:
    width, height = 2526, 1080
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    margin, gap, title_height, row_gap = 54, 27, 126, 27
    col_w = (width - 2 * margin - 3 * gap) / 4
    panel_h = (height - title_height - margin - row_gap) / 2
    draw.text((margin, 22), "Frozen EG07 formal layouts: deterministic before/after evidence", fill="black", font=font)
    draw.text((margin, 52), "Blue=subject; orange=object; gray=other. Top=original; bottom=gated repair.", fill="black", font=font)

    for col, example in enumerate(examples):
        x = margin + col * (col_w + gap)
        bbox = bounds(example)
        row = example["before_row"]
        heading = f"{example['room_type']} {'success' if example['kind'] == 'success' else 'remaining failure'}"
        draw.text((x, 86), heading, fill="black", font=font)
        draw.text((x, 104), f"{row['subject_class']} {row['predicate']} {row['object_class']}", fill="black", font=font)

        for layout, rel_row, top, label in (
            (example["before"], example["before_row"], title_height, "Original"),
            (example["after"], example["after_row"], title_height + panel_h + row_gap, "Gated repair"),
        ):
            panel = (x, top, col_w, panel_h)
            px, py, pw, ph = panel
            draw.rectangle((px, py, px + pw, py + ph), fill="#FAFBFC", outline=COLORS["grid"], width=2)
            scale, ox, oy_bottom = panel_transform(bbox, (px, 0, pw, ph))
            # Convert the PDF-style bottom-up y transform into image top-down coordinates.
            def to_image(world_x: float, world_z: float) -> tuple[float, float]:
                sx = ox + world_x * scale
                sy_from_bottom = oy_bottom + world_z * scale
                return sx, py + ph - sy_from_bottom

            for obj in layout["objects"]:
                role = object_role(int(obj["index"]), rel_row)
                cx, cy = to_image(float(obj["center"][0]), float(obj["center"][2]))
                hx = max(1.0, float(obj["size"][0]) * scale)
                hz = max(1.0, float(obj["size"][2]) * scale)
                angle = -float(obj.get("yaw", 0.0))
                corners = []
                for dx, dz in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)):
                    rx, rz = rotate_point(dx, dz, angle)
                    corners.append((cx + rx, cy + rz))
                draw.polygon(corners, fill=COLORS[role], outline=COLORS["outline"])
                if role != "other":
                    draw.text((cx - 22, cy - 6), short_category(obj["category"]), fill="black", font=font)
            satisfied = rel_row["is_satisfied"] == "1"
            draw.text((px + 8, py + 8), label, fill="black", font=font)
            draw.text(
                (px + pw - 42, py + 8),
                "PASS" if satisfied else "FAIL",
                fill=COLORS["pass"] if satisfied else COLORS["fail"],
                font=font,
            )
    image.save(path, format="PNG", optimize=True)


def serializable_selection(examples: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for example in examples:
        before_row = example["before_row"]
        after_row = example["after_row"]
        output.append(
            {
                "kind": example["kind"],
                "room_type": example["room_type"],
                "scene_id": example["scene_id"],
                "relation_id": example["relation_id"],
                "relation": {
                    "subject_class": before_row["subject_class"],
                    "predicate": before_row["predicate"],
                    "object_class": before_row["object_class"],
                },
                "baseline_satisfied": before_row["is_satisfied"] == "1",
                "main_satisfied": after_row["is_satisfied"] == "1",
                "gate_decision": example["after"].get("gate", {}).get("decision"),
            }
        )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--layouts",
        type=Path,
        default=root / "eg07_final_delivery_20260814" / "layouts" / "layouts.json",
    )
    parser.add_argument(
        "--per-relation",
        type=Path,
        default=root / "eg07_final_delivery_20260814" / "eg05" / "per_relation.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "paper" / "eurographics2027_submission" / "figures",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    layouts = load_layouts(args.layouts)
    relation_rows = read_csv(args.per_relation)
    examples = choose_examples(relation_rows, layouts)

    pdf_path = args.output_dir / "eg11_formal_qualitative.pdf"
    png_path = args.output_dir / "eg11_formal_qualitative.png"
    selection_path = args.output_dir / "eg11_formal_qualitative_selection.json"
    render_pdf(pdf_path, examples)
    render_png(png_path, examples)
    payload = {
        "schema": "eg2027-eg11-formal-qualitative-v1",
        "selection_rule": (
            "Lexicographically first evaluated baseline-fail/main-pass relation with nonzero XZ movement "
            "for each room; plus the lexicographically first evaluated baseline-fail/main-fail relation "
            "whose collision gate selected a nonzero-movement repair."
        ),
        "inputs": {
            "layouts": {"path": args.layouts.resolve().relative_to(root).as_posix(), "sha256": sha256(args.layouts)},
            "per_relation": {"path": args.per_relation.resolve().relative_to(root).as_posix(), "sha256": sha256(args.per_relation)},
        },
        "examples": serializable_selection(examples),
        "outputs": {
            "pdf": {"path": pdf_path.resolve().relative_to(root).as_posix(), "sha256": sha256(pdf_path)},
            "png": {"path": png_path.resolve().relative_to(root).as_posix(), "sha256": sha256(png_path), "mode": "RGB"},
        },
    }
    selection_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
