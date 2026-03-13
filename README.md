# Industrial PPE Training Pipeline - Stage 1 Bootstrap

This repository implements **Stage 1 bootstrap data preparation** for a warehouse/factory PPE detector.

Scope in this stage:
- Start from **public datasets only** (no customer/site-private data yet).
- Normalize labels into a single PPE schema.
- Merge datasets/splits into one final COCO layout.
- Validate annotation integrity.
- Generate stats and visualization samples.

This output is intended to be training-ready for NVIDIA TAO RT-DETR workflows on DGX.

---

## Project Structure

```text
.
├── configs/
│   └── tao_rtdetr_train.yaml
├── data/
│   ├── raw/
│   ├── interim/
│   └── final/
│       ├── train/images/
│       ├── val/images/
│       ├── test/images/
│       └── annotations/
├── logs/
├── run_pipeline.sh
└── scripts/
    ├── class_map.py
    ├── yolo_to_coco.py
    ├── remap_coco.py
    ├── merge_coco.py
    ├── check_coco.py
    ├── visualize_samples.py
    ├── stats_report.py
    └── download_placeholders.sh
```

---

## Target Final Classes (14)

1. person
2. helmet
3. vest
4. gloves
5. boots
6. goggles
7. mask
8. forklift
9. no_helmet
10. no_vest
11. no_gloves
12. no_boots
13. no_goggles
14. no_mask

`category_id` mapping is fixed to this order (1..14) in `scripts/class_map.py`.

---


## Detailed Download + Merge Runbook

For a concrete copy/paste guide (links, download steps, file placement, full multi-source command matrix for train/val/test, and pre-training checklist), see:

- `docs/DOWNLOAD_AND_MERGE_GUIDE.md`

---

## Supported Input Dataset Formats

### 1) YOLO format
Assumed split layout:

```text
data/raw/<dataset>/train/
  images/*.jpg|png
  labels/*.txt
  classes.txt
```

YOLO label line assumption:

```text
<class_idx> <x_center_norm> <y_center_norm> <width_norm> <height_norm>
```

### 2) COCO format
Assumed split layout:

```text
data/raw/<dataset>/
  images/<split>/*
  annotations/<split>.json
```

If your source uses a different folder naming scheme, update command arguments accordingly.

---

## Unified Class Mapping

`scripts/class_map.py` remaps common source labels into the target schema, including examples such as:
- worker -> person
- hardhat / hard-hat -> helmet
- reflective_vest / safety_vest -> vest
- glove / gloves -> gloves
- boot / boots / safety_boot -> boots
- goggle / goggles / safety_goggles -> goggles
- face_mask -> mask
- fork_lift -> forklift
- without_helmet -> no_helmet
- without_vest -> no_vest
- without_gloves -> no_gloves
- without_boots -> no_boots
- without_goggles -> no_goggles
- without_mask -> no_mask

Unknown source labels are dropped during remap and counted in logs.

---

## End-to-End Usage

> Python 3.10+ required.

### A) (Optional) Placeholders for data download

```bash
bash scripts/download_placeholders.sh
```

No auto-download is performed; manually place datasets under `data/raw/`.

### B) Convert YOLO to COCO

```bash
python3 scripts/yolo_to_coco.py \
  --images-dir data/raw/dataset_a_yolo/train/images \
  --labels-dir data/raw/dataset_a_yolo/train/labels \
  --class-names data/raw/dataset_a_yolo/classes.txt \
  --output-json data/interim/dataset_a_train_coco.json \
  --dataset-name dataset_a_train
```

### C) Remap COCO classes to target schema

```bash
python3 scripts/remap_coco.py \
  --input-json data/interim/dataset_a_train_coco.json \
  --output-json data/interim/dataset_a_train_remap.json
```

### D) Merge datasets into final split

```bash
python3 scripts/merge_coco.py \
  --input-jsons data/interim/dataset_a_train_remap.json data/interim/dataset_b_train_remap.json \
  --image-dirs data/raw/dataset_a_yolo/train/images data/raw/dataset_b_coco/images/train \
  --output-json data/final/annotations/train.json \
  --output-images-dir data/final/train/images \
  --copy-images
```

Repeat for `val` and `test`.

### E) Validate merged dataset

```bash
python3 scripts/check_coco.py --coco-json data/final/annotations/train.json --images-dir data/final/train/images --fail-on-error
```

Checks include:
- every annotation `category_id` valid
- every annotation `image_id` exists
- bbox width/height > 0
- class counts report
- missing image detection

### F) Generate stats and sample visualizations

```bash
python3 scripts/stats_report.py --coco-json data/final/annotations/train.json --output logs/train_stats.md
python3 scripts/visualize_samples.py --coco-json data/final/annotations/train.json --images-dir data/final/train/images --output-dir logs/viz/train --num-samples 25
```

### G) Run starter orchestration script

```bash
bash run_pipeline.sh
```

Update dataset paths in `run_pipeline.sh` to match your local `data/raw` contents.

---

## Script Reference

- `scripts/class_map.py`: canonical class list and synonym remapping.
- `scripts/yolo_to_coco.py`: YOLO split -> COCO JSON conversion.
- `scripts/remap_coco.py`: source COCO class IDs -> target class IDs.
- `scripts/merge_coco.py`: merges multiple remapped COCO files and copies images.
- `scripts/check_coco.py`: integrity checks and class count logging.
- `scripts/stats_report.py`: markdown stats summary.
- `scripts/visualize_samples.py`: draws bounding boxes/labels for sample QA.

---

## TAO RT-DETR Starter Config

See `configs/tao_rtdetr_train.yaml`.

You must edit placeholders such as:
- `results_dir`
- `pretrained_model_path`
- absolute dataset paths expected inside your DGX/TAO container
- optimizer/training parameters based on your hardware and TAO version

---

## Troubleshooting

- **`ModuleNotFoundError: PIL`**
  - Install Pillow: `pip install pillow`
- **No annotations after remap**
  - Source label names may not match known synonyms; extend `scripts/class_map.py`.
- **Missing image warnings in `check_coco.py`**
  - Verify that merge used `--copy-images` and correct `--image-dirs`.
- **Invalid bbox warnings**
  - Source labels may be malformed; inspect source txt/json and clean upstream.

---

## Assumptions (explicit)

1. Input YOLO datasets use normalized `xywh` bounding boxes.
2. YOLO class names are provided via a plain text class file (one class per line).
3. Source COCO files include standard fields: `images`, `annotations`, `categories`.
4. Segmentation/keypoints are out of scope in Stage 1 (bbox-only pipeline).
5. Merge script copies images and prefixes filenames to avoid collisions.
