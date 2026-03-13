#!/usr/bin/env bash
set -euo pipefail

# Stage 1 bootstrap pipeline (example orchestration)
# Assumes source datasets are manually placed under data/raw.

PYTHON=${PYTHON:-python3}

mkdir -p data/interim data/final/train/images data/final/val/images data/final/test/images data/final/annotations logs

# ---- Example dataset A (YOLO) conversion ----
# Edit paths to your actual dataset folder layout.
for SPLIT in train val test; do
  $PYTHON scripts/yolo_to_coco.py \
    --images-dir "data/raw/dataset_a_yolo/${SPLIT}/images" \
    --labels-dir "data/raw/dataset_a_yolo/${SPLIT}/labels" \
    --class-names data/raw/dataset_a_yolo/classes.txt \
    --output-json "data/interim/dataset_a_${SPLIT}_coco.json" \
    --dataset-name "dataset_a_${SPLIT}"

  $PYTHON scripts/remap_coco.py \
    --input-json "data/interim/dataset_a_${SPLIT}_coco.json" \
    --output-json "data/interim/dataset_a_${SPLIT}_remap.json"

done

# ---- Example dataset B (already COCO) remap ----
for SPLIT in train val test; do
  $PYTHON scripts/remap_coco.py \
    --input-json "data/raw/dataset_b_coco/annotations/${SPLIT}.json" \
    --output-json "data/interim/dataset_b_${SPLIT}_remap.json"
done

# ---- Merge final splits ----
for SPLIT in train val test; do
  $PYTHON scripts/merge_coco.py \
    --input-jsons "data/interim/dataset_a_${SPLIT}_remap.json" "data/interim/dataset_b_${SPLIT}_remap.json" \
    --image-dirs "data/raw/dataset_a_yolo/${SPLIT}/images" "data/raw/dataset_b_coco/images/${SPLIT}" \
    --output-json "data/final/annotations/${SPLIT}.json" \
    --output-images-dir "data/final/${SPLIT}/images" \
    --copy-images

done

# ---- Validation ----
for SPLIT in train val test; do
  $PYTHON scripts/check_coco.py \
    --coco-json "data/final/annotations/${SPLIT}.json" \
    --images-dir "data/final/${SPLIT}/images" \
    --fail-on-error

done

# ---- Stats ----
for SPLIT in train val test; do
  $PYTHON scripts/stats_report.py \
    --coco-json "data/final/annotations/${SPLIT}.json" \
    --output "logs/${SPLIT}_stats.md"
done

# ---- Visualization samples ----
for SPLIT in train val test; do
  $PYTHON scripts/visualize_samples.py \
    --coco-json "data/final/annotations/${SPLIT}.json" \
    --images-dir "data/final/${SPLIT}/images" \
    --output-dir "logs/viz/${SPLIT}" \
    --num-samples 25

done

echo "Pipeline completed for train/val/test. Update run_pipeline.sh paths for your datasets."
