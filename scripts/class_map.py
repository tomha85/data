#!/usr/bin/env python3
"""Unified PPE class mapping utilities.

This module defines the canonical target classes and a robust synonym mapping
layer used by conversion and remap scripts.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

TARGET_CLASSES: List[str] = [
    "person",
    "helmet",
    "vest",
    "gloves",
    "boots",
    "goggles",
    "mask",
    "forklift",
    "no_helmet",
    "no_vest",
    "no_gloves",
    "no_boots",
    "no_goggles",
    "no_mask",
]

TARGET_CLASS_TO_ID: Dict[str, int] = {name: i + 1 for i, name in enumerate(TARGET_CLASSES)}
TARGET_ID_TO_CLASS: Dict[int, str] = {i + 1: name for i, name in enumerate(TARGET_CLASSES)}

# Normalize common variations across public datasets.
_SYNONYM_TO_TARGET: Dict[str, str] = {
    "person": "person",
    "worker": "person",
    "human": "person",
    "hardhat": "helmet",
    "hard hat": "helmet",
    "hard-hat": "helmet",
    "helmet": "helmet",
    "safety helmet": "helmet",
    "vest": "vest",
    "reflective vest": "vest",
    "reflective_vest": "vest",
    "safety vest": "vest",
    "safety_vest": "vest",
    "high visibility vest": "vest",
    "glove": "gloves",
    "gloves": "gloves",
    "safety glove": "gloves",
    "safety gloves": "gloves",
    "boot": "boots",
    "boots": "boots",
    "safety boot": "boots",
    "safety boots": "boots",
    "safety_boot": "boots",
    "goggle": "goggles",
    "goggles": "goggles",
    "safety goggle": "goggles",
    "safety goggles": "goggles",
    "safety_goggles": "goggles",
    "mask": "mask",
    "face mask": "mask",
    "face_mask": "mask",
    "forklift": "forklift",
    "fork lift": "forklift",
    "fork_lift": "forklift",
    "without helmet": "no_helmet",
    "without_helmet": "no_helmet",
    "no helmet": "no_helmet",
    "without vest": "no_vest",
    "without_vest": "no_vest",
    "no vest": "no_vest",
    "without gloves": "no_gloves",
    "without_gloves": "no_gloves",
    "no gloves": "no_gloves",
    "without boots": "no_boots",
    "without_boots": "no_boots",
    "no boots": "no_boots",
    "without goggles": "no_goggles",
    "without_goggles": "no_goggles",
    "no goggles": "no_goggles",
    "without mask": "no_mask",
    "without_mask": "no_mask",
    "no mask": "no_mask",
}


def normalize_label(name: str) -> str:
    """Normalize source class labels for matching.

    Replaces punctuation/underscores with spaces and lowercases text.
    """
    stripped = name.strip().lower()
    stripped = re.sub(r"[_\-/]+", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped


def map_to_target(name: str) -> Optional[str]:
    """Map a source label into the target schema or return None when unknown."""
    if not name:
        return None
    normalized = normalize_label(name)
    if normalized in _SYNONYM_TO_TARGET:
        return _SYNONYM_TO_TARGET[normalized]
    if normalized in TARGET_CLASS_TO_ID:
        return normalized
    return None


def target_categories_coco() -> List[Dict[str, object]]:
    """Return COCO category objects for target classes."""
    return [
        {"id": TARGET_CLASS_TO_ID[name], "name": name, "supercategory": "ppe"}
        for name in TARGET_CLASSES
    ]


def parse_yolo_names_file(names_path: str) -> Dict[int, str]:
    """Parse a YOLO names file where each line is a class name."""
    mapping: Dict[int, str] = {}
    with open(names_path, "r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            name = line.strip()
            if name:
                mapping[idx] = name
    return mapping
