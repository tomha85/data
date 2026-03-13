#!/usr/bin/env python3
"""Remap source COCO classes into target PPE schema."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

from class_map import TARGET_CLASS_TO_ID, map_to_target, target_categories_coco


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remap COCO classes to target PPE schema")
    parser.add_argument("--input-json", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--drop-unmapped", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with args.input_json.open("r", encoding="utf-8") as handle:
        coco = json.load(handle)

    src_categories = coco.get("categories", [])
    src_id_to_name: Dict[int, str] = {int(c["id"]): str(c["name"]) for c in src_categories}

    remapped_annotations: List[Dict] = []
    dropped = 0
    for ann in coco.get("annotations", []):
        src_name = src_id_to_name.get(int(ann["category_id"]), "")
        target_name = map_to_target(src_name)
        if not target_name:
            dropped += 1
            continue
        new_ann = dict(ann)
        new_ann["category_id"] = TARGET_CLASS_TO_ID[target_name]
        remapped_annotations.append(new_ann)

    output = {
        "info": coco.get("info", {}),
        "licenses": coco.get("licenses", []),
        "images": coco.get("images", []),
        "annotations": remapped_annotations,
        "categories": target_categories_coco(),
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)

    logging.info(
        "Remap complete: kept=%d dropped=%d output=%s",
        len(remapped_annotations),
        dropped,
        args.output_json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
