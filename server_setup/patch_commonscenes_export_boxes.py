from pathlib import Path


TARGET = Path("/root/RelationAwareInstructScene/repos/commonscenes/scripts/eval_3dfront_export_boxes.py")


def main() -> None:
    source = TARGET.read_text()
    marker = "        all_pred_boxes.append(boxes_pred_den.cpu().detach())\n"
    insert = """        if export_3d:
            object_indices_exp = [int(x) for x in dec_objs.detach().cpu().numpy().tolist()]
            object_labels_exp = [testdataloader.dataset.classes_r.get(int(x), str(int(x))) for x in object_indices_exp]
            triples_exp = dec_triples.detach().cpu().numpy().astype(int).tolist()
            boxes_pred_exp = boxes_pred_den.detach().cpu().numpy().tolist()
            all_pred_boxes_exp[scan] = {
                "scan_id": scan,
                "instances": [str(x) for x in instances],
                "object_indices": object_indices_exp,
                "object_labels": object_labels_exp,
                "boxes_denormalized_xyzwhd": boxes_pred_exp,
                "triples_s_p_o": triples_exp,
            }

"""
    if insert.strip() in source:
        print(f"already patched: {TARGET}")
        return
    if marker not in source:
        raise SystemExit("marker not found")
    TARGET.write_text(source.replace(marker, insert + marker, 1))
    print(f"patched: {TARGET}")


if __name__ == "__main__":
    main()
