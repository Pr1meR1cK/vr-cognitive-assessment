# 基于 VR 接客任务的认知评估系统

本项目计划构建一个 Web 版认知评估系统，用于读取被试在 VR 四宫格/九宫格社区接客任务中的行为日志，并结合 MMSE、MoCA、CDR、HIS 量表结果，完成特征提取、相关性分析、风险建模、个体评估展示和报告导出。

## 当前状态

当前仓库提交的是 **算法代码、接口契约和演示流程**，不提交原始数据、训练结果、模型文件或临时数据集。

已具备：

```text
README 与项目说明
B 算法流程脚本
C 前端静态接口 JSON 生成脚本
mock 完整演示流程
算法/接口文档
```

尚需 A 接入：

```text
VR log 解析
四宫格/九宫格任务识别
_log_1/_log_2/_log_3 续存日志合并
grid4_*/grid9_*/overall_*/diff_* 特征提取
最终 merged_dataset.csv 输出
```

## 三人分工

A：数据处理负责人

```text
负责 VR 原始日志解析、任务类型识别、续存日志合并、量表读取、被试 ID 匹配、VR 行为特征提取，以及最终 merged_dataset.csv 输出。
```

B：算法模型负责人

```text
负责相关性分析、双特征组合分析、多量表候选模型、MoCA<26 风险模型、LOOCV 验证、模型注册表、用户预测报告和前端接口数据。
```

C：前端与系统集成负责人

```text
负责 Web 前端、接口调用、图表展示、个体评估页、报告展示/导出和系统演示。
```

## 数据约定

正式训练输入为：

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

其余数值列会自动作为候选特征，包括：

```text
grid4_*
grid9_*
overall_*
diff_*
drawing_*
```

用户预测阶段输入为 A 提取好的单人特征 JSON：

```json
{
  "subject_id": "ATH010002",
  "features": {
    "grid4_success_rate": 0.82,
    "grid9_success_rate": 0.61,
    "diff_success_rate": -0.21
  }
}
```

## B 算法脚本

核心脚本位于：

```text
scripts/
```

主要文件：

```text
cognitive_algorithm_core.py
run_cognitive_analysis.py
train_cognitive_model.py
generate_cognitive_results.py
predict_user_from_features.py
build_interim_merged_dataset.py
build_mock_full_dataset.py
build_frontend_api_payloads.py
```

说明：

```text
cognitive_algorithm_core.py       核心算法函数
run_cognitive_analysis.py         相关性和双特征组合分析
train_cognitive_model.py          多量表模型训练和模型注册表生成
generate_cognitive_results.py     完整 B 结果流程
predict_user_from_features.py     用户单人特征预测报告
build_interim_merged_dataset.py   临时合并量表与 drawing_* 特征
build_mock_full_dataset.py        生成 mock VR 特征用于演示
build_frontend_api_payloads.py    生成 C 前端静态 JSON 接口
```

## 模型策略

训练阶段会尝试生成：

```text
MMSE 分数模型
MOCA 分数模型
CDR_global 分数模型
CDR_SB 分数模型
HIS 分数模型
MOCA < 26 风险模型
```

模型是否进入用户报告由 `model_registry.json` 控制：

```text
trained           模型是否训练成功
enabled_for_user  是否允许展示给用户
quality_note      启用或暂不启用的原因
```

当前不设置人工固定权重。模型结果来自训练数据和 LOOCV 验证。

## C 前端接口

B 先提供静态 JSON 接口，后续可由 FastAPI 返回同样结构。

生成命令示例：

```powershell
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_mock_full/results --output-dir outputs/frontend_api_mock_full
```

接口文件：

```text
index.json
correlations.json
models.json
two_feature_analysis.json
subjects.json
subjects/{subject_id}.json
run_summary.json
```

接口说明见：

```text
docs/C_FRONTEND_API_CONTRACT.md
```

## Mock 演示流程

在 A 的真实 VR 特征尚未完成前，可以用 mock VR 特征跑通完整流程：

```powershell
python scripts/build_interim_merged_dataset.py --output outputs/interim_merged_dataset.csv
python scripts/build_mock_full_dataset.py --input outputs/interim_merged_dataset.csv --output outputs/mock_full_merged_dataset.csv
python scripts/generate_cognitive_results.py --input outputs/mock_full_merged_dataset.csv --output-dir outputs/cognitive_pipeline_mock_full --epochs 500
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_mock_full/results --output-dir outputs/frontend_api_mock_full
```

用户预测报告示例：

```powershell
python scripts/predict_user_from_features.py --features outputs/mock_user_upload/ATH010002_features.json --model-dir outputs/cognitive_pipeline_mock_full/model --output-dir outputs/user_prediction_mock_full
```

完整说明见：

```text
docs/MOCK_FULL_DEMO_FLOW.md
```

注意：mock VR 特征仅用于联调、演示和页面开发，不代表真实模型结论。

## 不提交的内容

以下内容不应提交到 GitHub：

```text
原始 VR log
MMSE_MoCA 原始 Excel
A_data
outputs
训练好的模型 JSON
模型指标 CSV
预测结果 CSV/JSON
mock/interim 数据集 CSV
用户报告 HTML
```

这些文件属于本地数据或运行产物。仓库只保留代码、文档和接口契约。
