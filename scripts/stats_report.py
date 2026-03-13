#!/usr/bin/env python3
"""Generate a readable dataset stats report from COCO JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate COCO stats report")
    parser.add_argument("--coco-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Path to markdown report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.coco_json.open("r", encoding="utf-8") as handle:
        coco = json.load(handle)

    id_to_class = {int(c["id"]): str(c["name"]) for c in coco.get("categories", [])}
    anns = coco.get("annotations", [])
    images = coco.get("images", [])

    class_counts = Counter(id_to_class.get(int(a["category_id"]), "unknown") for a in anns)
    image_ann_counts = Counter(int(a["image_id"]) for a in anns)

    lines = [
        "# COCO Dataset Stats",
        "",
        f"- Images: **{len(images)}**",
        f"- Annotations: **{len(anns)}**",
        f"- Categories: **{len(id_to_class)}**",
        f"- Empty images: **{sum(1 for img in images if int(img['id']) not in image_ann_counts)}**",
        "",
        "## Class Counts",
        "",
    ]

    for name in sorted(id_to_class.values()):
        lines.append(f"- {name}: {class_counts.get(name, 0)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote stats report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
