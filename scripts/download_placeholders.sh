#!/usr/bin/env bash
set -euo pipefail

# Placeholder helper only. Does not auto-download without user-provided credentials/IDs.
# Put downloaded datasets under data/raw/ as documented in README.

cat <<'EOF'
[Kaggle placeholder]
1) Authenticate first (kaggle.json in ~/.kaggle/).
2) Download manually, example:
   kaggle datasets download -d <owner>/<dataset-slug> -p data/raw/kaggle_downloads
3) Unzip and arrange structure under data/raw/<dataset_name>/...

[Roboflow placeholder]
1) Export dataset as YOLO or COCO in Roboflow UI.
2) If API key/project/version are available, example:
   curl -L "https://api.roboflow.com/dataset/<project>/<version>?api_key=<API_KEY>&format=coco" -o data/raw/roboflow_export.zip
3) Unzip and place into data/raw/<dataset_name>/...
EOF
