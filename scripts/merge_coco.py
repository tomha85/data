#!/usr/bin/env python3
"""Merge remapped COCO datasets into a single COCO file and image folder per split."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from class_map import target_categories_coco


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge multiple COCO datasets")
    parser.add_argument("--input-jsons", nargs="+", required=True, type=Path)
    parser.add_argument("--image-dirs", nargs="+", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-images-dir", required=True, type=Path)
    parser.add_argument("--copy-images", action="store_true", help="Copy source images into output image dir")
    parser.add_argument("--dataset-prefix", default="ds", help="Prefix used to avoid filename collisions")
    return parser.parse_args()


def load_coco(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(args.input_jsons) != len(args.image_dirs):
        raise ValueError("--input-jsons and --image-dirs must have the same number of entries")

    args.output_images_dir.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)

    merged_images: List[Dict] = []
    merged_annotations: List[Dict] = []
    next_image_id = 1
    next_ann_id = 1

    for idx, (json_path, image_dir) in enumerate(zip(args.input_jsons, args.image_dirs), start=1):
        coco = load_coco(json_path)
        old_to_new_image_id: Dict[int, int] = {}

        for img in coco.get("images", []):
            old_img_id = int(img["id"])
            src_file = image_dir / img["file_name"]
            safe_name = f"{args.dataset_prefix}{idx}_{img['file_name']}"
            dst_file = args.output_images_dir / safe_name

            if args.copy_images:
                if not src_file.exists():
                    logging.warning("Missing image while merging: %s", src_file)
                    continue
                shutil.copy2(src_file, dst_file)

            merged_images.append(
                {
                    "id": next_image_id,
                    "file_name": safe_name,
                    "width": int(img["width"]),
                    "height": int(img["height"]),
                }
            )
            old_to_new_image_id[old_img_id] = next_image_id
            next_image_id += 1

        for ann in coco.get("annotations", []):
            old_img_id = int(ann["image_id"])
            if old_img_id not in old_to_new_image_id:
                continue
            merged_ann = dict(ann)
            merged_ann["id"] = next_ann_id
            merged_ann["image_id"] = old_to_new_image_id[old_img_id]
            merged_annotations.append(merged_ann)
            next_ann_id += 1

    out = {
        "info": {"description": "Merged PPE bootstrap dataset"},
        "licenses": [],
        "images": merged_images,
        "annotations": merged_annotations,
        "categories": target_categories_coco(),
    }

    with args.output_json.open("w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)

    logging.info("Merged %d images and %d annotations", len(merged_images), len(merged_annotations))
    logging.info("Output JSON: %s", args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
