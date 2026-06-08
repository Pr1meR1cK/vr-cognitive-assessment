# VR Cognitive Assessment Project Delivery Status

Date: 2026-06-08

This repository contains the shareable project code and documentation for the VR cognitive assessment system. It intentionally does not include raw datasets, real subject CSV files, trained model JSON files, generated reports, or pipeline outputs.

## Team Scope

A: data processing and feature extraction.

- VR behavior log parsing.
- Drawing/handwriting feature extraction.
- Scale score reading and subject ID alignment.
- Final `merged_dataset.csv` construction.

B: algorithm, model, prediction, and report interface.

- Correlation analysis.
- Two-feature exploratory analysis.
- Risk/score model training.
- LOOCV validation.
- User-facing prediction report generation.
- Static JSON payload generation for C.

C: frontend and system integration.

- Web UI.
- API/static JSON integration.
- Visualization pages.
- Individual assessment page and report display/export.

## A Files Added To Repository

A's shareable algorithm files are now stored here:

```text
scripts/a_data_pipeline/
  build_merged_dataset.py
  extract_drawing_features.py

docs/a_algorithm/
  README.md
  01_drawing_feature_extraction.md
  02_vr_behavior_feature_extraction.md
  03_dataset_building.md
```

The following A files are not committed because they are real data or generated outputs:

```text
A_data/output1/merged_dataset.csv
A_data/output1/scale_scores.csv
A_data/output1/vr_features.csv
A_data/output3/*.csv
```

## B Files Added To Repository

B's current algorithm workflow is stored here:

```text
scripts/cognitive_algorithm_core.py
scripts/train_cognitive_model.py
scripts/run_cognitive_analysis.py
scripts/generate_cognitive_results.py
scripts/predict_user_from_features.py
scripts/build_frontend_api_payloads.py
scripts/build_interim_merged_dataset.py
scripts/build_mock_full_dataset.py
```

## Current B Main Model

After testing all-feature, core-feature, and selected-feature strategies, the default B workflow now uses:

```text
feature_set = selected
model_top_k = 5
```

The current user-facing model is:

```text
Target: MOCA < 26
Model: Logistic Regression with L2
Validation: LOOCV
Rows: 37
Positive: 20
Negative: 17
AUC: 0.679
Accuracy: 0.649
Sensitivity: 0.800
Specificity: 0.471
F1: 0.711
```

Selected features:

```text
grid4_map_ratio
drawing_moca_cube_intersection_count
drawing_moca_trail_crossing_count
drawing_moca_trail_duration
overall_map_ratio
```

MMSE, MOCA score, CDR, CDR-SB, and HIS score prediction models are kept as research outputs only. They are not enabled for the user-facing report because LOOCV regression quality is not stable enough under the current sample size.

MMSE/CDR/HIS risk targets are also trained and evaluated, but they are not enabled for the user-facing report unless `model_registry.json` marks them as `enabled_for_user: true`.

## Recommended Real Data Commands

Run full B pipeline:

```bash
python scripts/generate_cognitive_results.py --input path/to/merged_dataset.csv --output-dir outputs/cognitive_pipeline_real
```

Generate frontend static JSON payloads:

```bash
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_real/results --output-dir outputs/frontend_api_real
```

The default command already uses selected features and top 5 model features.

## Frontend Contract

C should read:

```text
outputs/frontend_api_real/index.json
outputs/frontend_api_real/models.json
outputs/frontend_api_real/subjects.json
outputs/frontend_api_real/subjects/{subject_id}.json
```

The subject payload keeps the old single `risk` field and also includes a `risks` list for future multi-risk display.

## Do Not Commit

Do not commit:

```text
A_data/
outputs/
trained_models/
*.xlsx
*.xls
*_model.json
model_registry.json
subject_risk/
real merged datasets
generated report files
```

These are already covered by `.gitignore`.
