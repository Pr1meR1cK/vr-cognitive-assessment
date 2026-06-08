# B 算法流程说明

当前 B 模块分为两条流程：

```text
离线训练流程：merged_dataset.csv -> 多模型训练 -> model_registry.json
用户预测流程：单人 VR 特征 JSON -> 加载可用模型 -> user_prediction.json + user_report.html
```

原始单文件验证版仍保留：

```text
scripts/adaptive_cognitive_algorithm.py
```

正式草稿文件：

```text
scripts/cognitive_algorithm_core.py
scripts/run_cognitive_analysis.py
scripts/train_cognitive_model.py
scripts/generate_cognitive_results.py
scripts/predict_user_from_features.py
scripts/build_interim_merged_dataset.py
```

## 0. 临时数据集流程

在 A 的 VR 特征尚未完成时，可以先用现有量表 Excel 和 A 已给的笔迹特征构建临时训练集：

```powershell
python scripts/build_interim_merged_dataset.py --output outputs/interim_merged_dataset.csv
```

该临时表包含：

```text
subject_id
MMSE
MOCA
CDR_global
CDR_SB
HIS
drawing_*
```

不包含：

```text
grid4_*
grid9_*
overall_*
diff_*
```

所以它只能用于提前验证 B 的训练、模型注册、用户报告链路，不能替代最终 VR 数据模型。

## 1. 离线训练流程

入口：

```powershell
python scripts/train_cognitive_model.py --input examples/mock_merged_dataset.csv --model-dir outputs/trained_models
```

输入仍然是 A 给 B 的训练数据：

```text
merged_dataset.csv
```

必须包含：

```text
subject_id
MMSE
MOCA
CDR_global
CDR_SB
HIS
```

其余数值列自动作为候选特征：

```text
grid4_*
grid9_*
overall_*
diff_*
drawing_*
```

训练脚本会尝试生成：

```text
MMSE_score_model.json
MOCA_score_model.json
CDR_global_score_model.json
CDR_SB_score_model.json
HIS_score_model.json
MOCA_risk_model.json
model_registry.json
```

其中 `model_registry.json` 记录当前哪些模型训练成功。后续真实数据跑完后，如果某个目标样本不足或分布不合适，该模型可以不启用，不影响其他模型。

模型注册表里有两个不同状态：

```text
trained: 模型是否训练成功
enabled_for_user: 是否允许进入用户报告
```

目前默认规则：

```text
分数回归模型：LOOCV R2 > 0 且 |Pearson r| >= 0.3 才进入用户报告
风险分类模型：LOOCV AUC >= 0.6 才进入用户报告
```

因此某些模型可能已经训练成功，但由于验证质量不足，只保留在内部结果中，不展示给用户。

## 2. 研究分析结果

入口：

```powershell
python scripts/generate_cognitive_results.py --input examples/mock_merged_dataset.csv --output-dir outputs/cognitive_pipeline
```

给 C 或后端查看的集中结果目录：

```text
outputs/cognitive_pipeline/results/
```

包含：

```text
correlations.csv
correlations_reliable_n10.csv
two_feature_analysis.csv
model_metrics.csv
score_model_metrics.csv
feature_importance.csv
score_loocv_predictions.csv
model_predictions.csv
model_registry.json
run_summary.json
subject_risk/*.json
```

这些文件用于模型验证、系统展示和内部分析，不等同于最终用户上传 VR log 后看到的报告。

## 3. 用户预测流程

用户预测阶段不需要真实量表分数。

A 先把用户上传的 VR log 解析成单人特征 JSON：

```json
{
  "subject_id": "ATH010001",
  "features": {
    "grid4_success_rate": 0.85,
    "grid9_success_rate": 0.62,
    "diff_success_rate": -0.23
  }
}
```

B 调用：

```powershell
python scripts/predict_user_from_features.py --features outputs/user_feature.json --model-dir outputs/trained_models --output-dir outputs/user_prediction
```

输出：

```text
outputs/user_prediction/user_prediction.json
outputs/user_prediction/user_report.html
outputs/user_prediction/prediction_summary.json
```

`user_prediction.json` 使用稳定数组结构，后续可扩展更多模型：

```json
{
  "subject_id": "ATH010001",
  "predictions": [
    {
      "target": "MOCA",
      "type": "score",
      "value": 23.4
    },
    {
      "target": "MOCA < 26",
      "type": "risk",
      "probability": 0.68,
      "score": 68,
      "level": "中风险"
    }
  ],
  "key_findings": [],
  "data_quality": {
    "input_feature_count": 18,
    "model_count": 2,
    "missing_model_features": []
  },
  "model_basis": {
    "input": "VR log behavior features",
    "note": "探索性辅助评估，不代表临床诊断。"
  }
}
```

## 4. 可扩展性约定

当前不设置固定人工权重。

模型目标、启用哪些模型、关键解释特征，都可以在真实数据跑完后调整。C 侧只需要依赖稳定字段：

```text
subject_id
predictions[]
key_findings[]
data_quality
model_basis
```

A 可以继续调整特征数量和字段，只要保持数值列和命名前缀即可：

```text
grid4_*
grid9_*
overall_*
diff_*
drawing_*
```

用户预测时如果缺少某些模型需要的特征，B 会用训练均值补齐，并在 `data_quality.missing_model_features` 中记录。

## 5. 当前默认

第一版会尝试训练四类量表相关目标：

```text
MMSE 分数
MOCA 分数
CDR_global 分数/等级近似值
CDR_SB 分数
HIS 分数
MOCA < 26 风险
```

真实数据跑完后，再决定哪些模型正式展示给用户。
