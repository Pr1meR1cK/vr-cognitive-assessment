# C 前端静态接口说明

当前仓库还没有正式后端服务，因此 B 先提供静态 JSON 接口文件。C 可以直接读取这些 JSON 开发页面；后续接 FastAPI 时保持相同返回结构即可。

生成命令：

```powershell
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_interim_drawing_quality/results --output-dir outputs/frontend_api
```

接口目录：

```text
outputs/frontend_api/
```

## 1. 接口索引

```text
index.json
```

用途：告诉前端当前可用接口文件。

主要字段：

```text
api_version
files.correlations
files.models
files.two_feature_analysis
files.subjects
files.run_summary
subject_detail_pattern
```

## 2. 相关性页面

```text
correlations.json
```

对应页面：

```text
单维度相关 Top 指标页
```

主要字段：

```text
summary.row_count
summary.targets
top_by_target
all
```

`top_by_target` 按量表目标分组，例如：

```text
MMSE
MOCA
CDR_global
CDR_SB
HIS
```

每条相关性包含：

```text
target
feature
n
pearson_r
spearman_r
abs_spearman_r
sample_note
```

## 3. 双特征组合页面

```text
two_feature_analysis.json
```

对应页面：

```text
双维度组合分析页
```

主要字段：

```text
summary.row_count
top
all
```

每条组合包含：

```text
target
feature_a
feature_b
n
R
R2
adjusted_R2
F_stat
note
```

## 4. 模型评估页面

```text
models.json
```

对应页面：

```text
模型评估页
```

主要字段：

```text
registry
risk_metrics
score_metrics
feature_importance
```

注意：

```text
registry.models[].trained
registry.models[].enabled_for_user
registry.models[].quality_note
```

含义：

```text
trained = 模型是否训练成功
enabled_for_user = 是否进入用户报告展示
quality_note = 为什么启用或暂不启用
```

## 5. 被试列表

```text
subjects.json
```

对应页面：

```text
个体风险列表页
```

结构：

```json
{
  "subjects": [
    {
      "subject_id": "ATH010002",
      "risk": {
        "probability": 0.72,
        "score": 72,
        "level": "高风险"
      },
      "detail_url": "subjects/ATH010002.json"
    }
  ]
}
```

## 6. 被试详情

```text
subjects/{subject_id}.json
```

对应页面：

```text
个体风险解释页
报告页
```

主要字段：

```text
subject_id
risk
prediction
model_basis
selected_features
```

其中 `prediction` 来自模型预测表，包含：

```text
MOCA
true_moca_risk
risk_probability
risk_score
risk_level
predicted_label
selected_features
```

当前这是基于训练/验证数据的个体结果。真正用户上传 VR log 后，使用 `predict_user_from_features.py` 生成的：

```text
user_prediction.json
user_report.html
```

## 7. 前端建议

第一版页面可以先接：

```text
index.json
correlations.json
models.json
subjects.json
subjects/{subject_id}.json
```

暂时不要把 `score_metrics` 里质量不足的分数模型作为用户结论展示。是否展示以：

```text
enabled_for_user
```

为准。
