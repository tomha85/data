#!/usr/bin/env python3
"""Validate COCO annotations for PPE pipeline quality checks."""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate COCO annotation file")
    parser.add_argument("--coco-json", required=True, type=Path)
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with args.coco_json.open("r", encoding="utf-8") as handle:
        coco = json.load(handle)

    valid_cat_ids = {int(c["id"]) for c in coco.get("categories", [])}
    cat_name = {int(c["id"]): c["name"] for c in coco.get("categories", [])}
    image_ids = {int(i["id"]) for i in coco.get("images", [])}
    image_files = {i["file_name"] for i in coco.get("images", [])}

    invalid_category = 0
    invalid_image_ref = 0
    invalid_bbox = 0

    per_class = Counter()

    for ann in coco.get("annotations", []):
        cid = int(ann["category_id"])
        iid = int(ann["image_id"])
        bbox = ann.get("bbox", [0, 0, 0, 0])

        if cid not in valid_cat_ids:
            invalid_category += 1
        else:
            per_class[cat_name[cid]] += 1

        if iid not in image_ids:
            invalid_image_ref += 1

        if len(bbox) != 4 or float(bbox[2]) <= 0 or float(bbox[3]) <= 0:
            invalid_bbox += 1

    missing_images = [name for name in sorted(image_files) if not (args.images_dir / name).exists()]

    logging.info("Validation summary for %s", args.coco_json)
    logging.info("Images: %d", len(image_ids))
    logging.info("Annotations: %d", len(coco.get("annotations", [])))
    logging.info("Invalid category refs: %d", invalid_category)
    logging.info("Invalid image refs: %d", invalid_image_ref)
    logging.info("Invalid bbox entries: %d", invalid_bbox)
    logging.info("Missing image files: %d", len(missing_images))

    for cls_name, count in sorted(per_class.items()):
        logging.info("Class count %-12s : %d", cls_name, count)

    if missing_images:
        logging.warning("First 20 missing images: %s", missing_images[:20])

    has_error = any([invalid_category, invalid_image_ref, invalid_bbox, len(missing_images)])
    if has_error and args.fail_on_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
