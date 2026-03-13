#!/usr/bin/env python3
"""Convert YOLO-format split into COCO JSON.

Expected structure (per split):
- images/  (image files)
- labels/  (txt files with same stem as image files)

Class names can be loaded from data.yaml or a names file.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert YOLO annotations to COCO format")
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--labels-dir", required=True, type=Path)
    parser.add_argument("--class-names", required=True, type=Path, help="Text file, one class name per line")
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--dataset-name", default="yolo_source")
    return parser.parse_args()


def load_class_names(path: Path) -> List[str]:
    names: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            candidate = line.strip()
            if candidate:
                names.append(candidate)
    if not names:
        raise ValueError(f"No class names found in {path}")
    return names


def collect_images(images_dir: Path) -> List[Path]:
    supported = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    return sorted([p for p in images_dir.iterdir() if p.suffix.lower() in supported])


def yolo_to_bbox(values: Tuple[float, float, float, float], width: int, height: int) -> List[float]:
    x_center, y_center, box_w, box_h = values
    bw = box_w * width
    bh = box_h * height
    x = (x_center * width) - (bw / 2.0)
    y = (y_center * height) - (bh / 2.0)
    return [round(x, 2), round(y, 2), round(bw, 2), round(bh, 2)]


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not args.images_dir.exists() or not args.labels_dir.exists():
        raise FileNotFoundError("images-dir and labels-dir must both exist")

    class_names = load_class_names(args.class_names)
    images = []
    annotations = []
    categories = [{"id": idx + 1, "name": name, "supercategory": "source"} for idx, name in enumerate(class_names)]

    image_id = 1
    annotation_id = 1

    for image_path in collect_images(args.images_dir):
        label_path = args.labels_dir / f"{image_path.stem}.txt"
        with Image.open(image_path) as img:
            width, height = img.size

        images.append(
            {
                "id": image_id,
                "file_name": image_path.name,
                "width": width,
                "height": height,
            }
        )

        if label_path.exists():
            with label_path.open("r", encoding="utf-8") as handle:
                for line_num, line in enumerate(handle, start=1):
                    parts = line.strip().split()
                    if len(parts) != 5:
                        logging.warning("Skipping malformed line %s in %s", line_num, label_path)
                        continue
                    cls_idx = int(parts[0])
                    if cls_idx < 0 or cls_idx >= len(class_names):
                        logging.warning("Skipping class index %s in %s", cls_idx, label_path)
                        continue
                    x, y, w, h = map(float, parts[1:])
                    bbox = yolo_to_bbox((x, y, w, h), width, height)
                    if bbox[2] <= 0 or bbox[3] <= 0:
                        continue
                    annotations.append(
                        {
                            "id": annotation_id,
                            "image_id": image_id,
                            "category_id": cls_idx + 1,
                            "bbox": bbox,
                            "area": round(bbox[2] * bbox[3], 2),
                            "iscrowd": 0,
                        }
                    )
                    annotation_id += 1

        image_id += 1

    output = {
        "info": {"description": args.dataset_name},
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    logging.info("Wrote COCO JSON: %s (images=%d, annotations=%d)", args.output_json, len(images), len(annotations))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
