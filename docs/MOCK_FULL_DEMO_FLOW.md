# 完整 Mock 演示流程

由于 A 的真实 VR 特征暂未完成，当前先用模拟 VR 特征把完整 B 流程跑通。该流程只用于联调、演示和页面开发，不作为真实模型结论。

## 1. 构建临时基础数据

```powershell
python scripts/build_interim_merged_dataset.py --output outputs/interim_merged_dataset.csv
```

来源：

```text
MMSE_MoCA/*.xlsx
A_data/output3/drawing_features.csv
```

输出：

```text
outputs/interim_merged_dataset.csv
```

包含：

```text
subject_id
MMSE
MOCA
CDR_global
CDR_SB
HIS
drawing_*
```

## 2. 模拟 VR 特征

```powershell
python scripts/build_mock_full_dataset.py --input outputs/interim_merged_dataset.csv --output outputs/mock_full_merged_dataset.csv
```

输出：

```text
outputs/mock_full_merged_dataset.csv
```

包含：

```text
subject_id
MMSE
MOCA
CDR_global
CDR_SB
HIS
grid4_*
grid9_*
overall_*
diff_*
drawing_*
```

注意：`grid4_*`、`grid9_*`、`overall_*`、`diff_*` 是模拟数据，只用于演示完整流程。

## 3. 跑完整 B 流程

```powershell
python scripts/generate_cognitive_results.py --input outputs/mock_full_merged_dataset.csv --output-dir outputs/cognitive_pipeline_mock_full --epochs 500
```

输出目录：

```text
outputs/cognitive_pipeline_mock_full/results/
```

包含：

```text
correlations.csv
two_feature_analysis.csv
model_registry.json
model_metrics.csv
score_model_metrics.csv
model_predictions.csv
subject_risk/*.json
```

## 4. 生成 C 前端接口

```powershell
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_mock_full/results --output-dir outputs/frontend_api_mock_full
```

C 使用：

```text
outputs/frontend_api_mock_full/index.json
outputs/frontend_api_mock_full/correlations.json
outputs/frontend_api_mock_full/models.json
outputs/frontend_api_mock_full/two_feature_analysis.json
outputs/frontend_api_mock_full/subjects.json
outputs/frontend_api_mock_full/subjects/{subject_id}.json
```

## 5. 模拟用户上传后的预测报告

先构造单人特征 JSON：

```text
outputs/mock_user_upload/ATH010002_features.json
```

再运行：

```powershell
python scripts/predict_user_from_features.py --features outputs/mock_user_upload/ATH010002_features.json --model-dir outputs/cognitive_pipeline_mock_full/model --output-dir outputs/user_prediction_mock_full
```

输出：

```text
outputs/user_prediction_mock_full/user_prediction.json
outputs/user_prediction_mock_full/user_report.html
outputs/user_prediction_mock_full/prediction_summary.json
```

## 6. 当前演示结果

本次 mock full 数据：

```text
样本数：37
总列数：178
模拟 VR 特征数：80
候选模型特征数：172
```

训练出的模型：

```text
MMSE 分数模型
MOCA 分数模型
CDR_global 分数模型
CDR_SB 分数模型
HIS 分数模型
MOCA<26 风险模型
```

进入用户报告的模型以 `model_registry.json` 中的 `enabled_for_user` 为准。

真实 A 数据到位后，只需要用真实 `merged_dataset.csv` 替换：

```text
outputs/mock_full_merged_dataset.csv
```

后续脚本不需要重写。
