#!/usr/bin/env python3
"""Generate sample visualization images with bounding boxes and labels."""

from __future__ import annotations

import argparse
import json
import logging
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize COCO annotations")
    parser.add_argument("--coco-json", required=True, type=Path)
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--num-samples", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with args.coco_json.open("r", encoding="utf-8") as handle:
        coco = json.load(handle)

    id_to_image = {int(i["id"]): i for i in coco.get("images", [])}
    id_to_class = {int(c["id"]): str(c["name"]) for c in coco.get("categories", [])}
    image_to_anns = defaultdict(list)
    for ann in coco.get("annotations", []):
        image_to_anns[int(ann["image_id"])].append(ann)

    ids = sorted(image_to_anns.keys())
    random.seed(args.seed)
    random.shuffle(ids)
    selected = ids[: min(args.num_samples, len(ids))]

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for image_id in selected:
        info = id_to_image.get(image_id)
        if not info:
            continue
        src = args.images_dir / info["file_name"]
        if not src.exists():
            logging.warning("Missing image for visualization: %s", src)
            continue

        with Image.open(src).convert("RGB") as im:
            draw = ImageDraw.Draw(im)
            for ann in image_to_anns[image_id]:
                x, y, w, h = ann["bbox"]
                cls_name = id_to_class.get(int(ann["category_id"]), "unknown")
                draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                draw.text((x + 3, y + 3), cls_name, fill="yellow")
            dst = args.output_dir / f"viz_{image_id}_{src.name}"
            im.save(dst)

    logging.info("Visualization samples written to %s", args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
