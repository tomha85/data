# Detailed Guide: Download Public PPE Datasets, Prepare, and Merge

This guide is a concrete runbook for **Stage 1 bootstrap** data prep.
It covers:
1. Where to download datasets.
2. How to place files in `data/raw`.
3. How to convert/remap/merge all splits.
4. Validation and quality gates before training.

---

## 1) Recommended public sources (with links)

Use at least 2-3 sources for better coverage.

- Roboflow Universe search (PPE and safety):
  - https://universe.roboflow.com/search?q=ppe
  - https://universe.roboflow.com/search?q=construction%20safety
- Kaggle dataset search:
  - https://www.kaggle.com/datasets?search=ppe
  - https://www.kaggle.com/datasets?search=construction+safety

> License note: verify each dataset's license allows your intended use.

---

## 2) Download each source

## Source A: Roboflow YOLO export

1. Open a dataset page in Roboflow Universe.
2. Click **Download / Export**.
3. Choose **YOLOv5** or **YOLOv8** format.
4. Download zip.
5. Unzip to `data/raw/source_a_yolo/`.

Expected end state:

```text
data/raw/source_a_yolo/
  train/images
  train/labels
  val/images
  val/labels
  test/images
  test/labels
  classes.txt
```

If source provides `valid/` instead of `val/`, either rename it or use that path directly in commands.

## Source B: Kaggle YOLO export (or converted structure)

```bash
# 1) Authenticate (one-time)
mkdir -p ~/.kaggle
cp /path/to/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

# 2) Download
kaggle datasets download -d <owner>/<dataset-slug> -p data/raw/kaggle_downloads

# 3) Unzip
unzip data/raw/kaggle_downloads/<archive>.zip -d data/raw/source_b_yolo
```

Then reorganize files to the same YOLO split layout shown above.

## Source C: COCO dataset

Download source zip and unpack to:

```text
data/raw/source_c_coco/
  images/train/*
  images/val/*
  images/test/*
  annotations/train.json
  annotations/val.json
  annotations/test.json
```

---

## 3) Install dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install pillow
```

---

## 4) Full processing command matrix (copy/paste template)

## 4.1 Convert YOLO -> COCO (source A + source B)

```bash
# Train
python3 scripts/yolo_to_coco.py --images-dir data/raw/source_a_yolo/train/images --labels-dir data/raw/source_a_yolo/train/labels --class-names data/raw/source_a_yolo/classes.txt --output-json data/interim/source_a_train_coco.json --dataset-name source_a_train
python3 scripts/yolo_to_coco.py --images-dir data/raw/source_b_yolo/train/images --labels-dir data/raw/source_b_yolo/train/labels --class-names data/raw/source_b_yolo/classes.txt --output-json data/interim/source_b_train_coco.json --dataset-name source_b_train

# Val
python3 scripts/yolo_to_coco.py --images-dir data/raw/source_a_yolo/val/images --labels-dir data/raw/source_a_yolo/val/labels --class-names data/raw/source_a_yolo/classes.txt --output-json data/interim/source_a_val_coco.json --dataset-name source_a_val
python3 scripts/yolo_to_coco.py --images-dir data/raw/source_b_yolo/val/images --labels-dir data/raw/source_b_yolo/val/labels --class-names data/raw/source_b_yolo/classes.txt --output-json data/interim/source_b_val_coco.json --dataset-name source_b_val

# Test
python3 scripts/yolo_to_coco.py --images-dir data/raw/source_a_yolo/test/images --labels-dir data/raw/source_a_yolo/test/labels --class-names data/raw/source_a_yolo/classes.txt --output-json data/interim/source_a_test_coco.json --dataset-name source_a_test
python3 scripts/yolo_to_coco.py --images-dir data/raw/source_b_yolo/test/images --labels-dir data/raw/source_b_yolo/test/labels --class-names data/raw/source_b_yolo/classes.txt --output-json data/interim/source_b_test_coco.json --dataset-name source_b_test
```

## 4.2 Remap all COCO files into target PPE schema

```bash
# source A
python3 scripts/remap_coco.py --input-json data/interim/source_a_train_coco.json --output-json data/interim/source_a_train_remap.json
python3 scripts/remap_coco.py --input-json data/interim/source_a_val_coco.json --output-json data/interim/source_a_val_remap.json
python3 scripts/remap_coco.py --input-json data/interim/source_a_test_coco.json --output-json data/interim/source_a_test_remap.json

# source B
python3 scripts/remap_coco.py --input-json data/interim/source_b_train_coco.json --output-json data/interim/source_b_train_remap.json
python3 scripts/remap_coco.py --input-json data/interim/source_b_val_coco.json --output-json data/interim/source_b_val_remap.json
python3 scripts/remap_coco.py --input-json data/interim/source_b_test_coco.json --output-json data/interim/source_b_test_remap.json

# source C (already COCO)
python3 scripts/remap_coco.py --input-json data/raw/source_c_coco/annotations/train.json --output-json data/interim/source_c_train_remap.json
python3 scripts/remap_coco.py --input-json data/raw/source_c_coco/annotations/val.json --output-json data/interim/source_c_val_remap.json
python3 scripts/remap_coco.py --input-json data/raw/source_c_coco/annotations/test.json --output-json data/interim/source_c_test_remap.json
```

## 4.3 Merge remapped datasets per split

```bash
# Train merge
python3 scripts/merge_coco.py \
  --input-jsons data/interim/source_a_train_remap.json data/interim/source_b_train_remap.json data/interim/source_c_train_remap.json \
  --image-dirs data/raw/source_a_yolo/train/images data/raw/source_b_yolo/train/images data/raw/source_c_coco/images/train \
  --output-json data/final/annotations/train.json \
  --output-images-dir data/final/train/images \
  --copy-images

# Val merge
python3 scripts/merge_coco.py \
  --input-jsons data/interim/source_a_val_remap.json data/interim/source_b_val_remap.json data/interim/source_c_val_remap.json \
  --image-dirs data/raw/source_a_yolo/val/images data/raw/source_b_yolo/val/images data/raw/source_c_coco/images/val \
  --output-json data/final/annotations/val.json \
  --output-images-dir data/final/val/images \
  --copy-images

# Test merge
python3 scripts/merge_coco.py \
  --input-jsons data/interim/source_a_test_remap.json data/interim/source_b_test_remap.json data/interim/source_c_test_remap.json \
  --image-dirs data/raw/source_a_yolo/test/images data/raw/source_b_yolo/test/images data/raw/source_c_coco/images/test \
  --output-json data/final/annotations/test.json \
  --output-images-dir data/final/test/images \
  --copy-images
```

---

## 5) Validate merged output (before training)

```bash
python3 scripts/check_coco.py --coco-json data/final/annotations/train.json --images-dir data/final/train/images --fail-on-error
python3 scripts/check_coco.py --coco-json data/final/annotations/val.json --images-dir data/final/val/images --fail-on-error
python3 scripts/check_coco.py --coco-json data/final/annotations/test.json --images-dir data/final/test/images --fail-on-error
```

---

## 6) Generate stats + visual QA artifacts

```bash
python3 scripts/stats_report.py --coco-json data/final/annotations/train.json --output logs/train_stats.md
python3 scripts/stats_report.py --coco-json data/final/annotations/val.json --output logs/val_stats.md
python3 scripts/stats_report.py --coco-json data/final/annotations/test.json --output logs/test_stats.md

python3 scripts/visualize_samples.py --coco-json data/final/annotations/train.json --images-dir data/final/train/images --output-dir logs/viz/train --num-samples 25
python3 scripts/visualize_samples.py --coco-json data/final/annotations/val.json --images-dir data/final/val/images --output-dir logs/viz/val --num-samples 25
python3 scripts/visualize_samples.py --coco-json data/final/annotations/test.json --images-dir data/final/test/images --output-dir logs/viz/test --num-samples 25
```

---

## 7) Checklist before main training

- `data/final/annotations/train.json`, `val.json`, `test.json` exist.
- Image folders are populated for train/val/test.
- All `check_coco.py --fail-on-error` commands pass.
- Stats and visualizations look correct.
- Unknown/dropped classes are reviewed and mapping extended if needed.
