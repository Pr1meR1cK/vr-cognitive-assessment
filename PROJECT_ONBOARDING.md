# 项目同步说明：基于 VR 接客任务的认知评估系统

这个文件用于在新电脑、新成员或新分支环境中快速同步项目信息。  
如果你是第一次接手本项目，请先读本文件，再读 `README.md` 和 `team_workflow_github_desktop.html`。

## 1. 项目在做什么

本项目希望做成一个 Web 网页应用：

> 读取被试在 VR 四宫格/九宫格社区接客任务中的行为日志，结合 MMSE、MoCA、CDR、HIS 等传统量表，完成数据处理、行为特征提取、相关性分析、认知风险建模、个体评估展示和报告导出。

当前不是单纯写一个模型，而是要实现一个完整的认知评估系统。

系统流程如下：

```text
VR 日志 + 量表 Excel
        ↓
数据清洗与被试匹配
        ↓
四宫格/九宫格任务识别
        ↓
行为特征提取
        ↓
相关性分析
        ↓
风险模型训练
        ↓
Web 页面展示
        ↓
个体报告导出
```

## 2. 当前项目状态

已经完成：

- VR 日志解析
- 四宫格 / 九宫格任务识别
- `_log_1`、`_log_2` 等续存日志处理
- 空日志剔除
- MMSE、MoCA、CDR、HIS 量表读取
- 被试 ID 自动匹配
- VR 行为特征提取
- 量表与 VR 特征合并
- 相关性分析
- 中文 README
- 三人协作 HTML 文档

尚未正式完成：

- 认知风险模型训练
- FastAPI 后端服务
- Web 前端页面
- 报告导出模块

注意：`scripts/train_cognitive_model.py` 是模型训练草稿，尚未正式跑通和验证，不能直接作为最终模型结果。

## 3. 当前有效数据结果

最新有效分析输出：

```text
outputs/correlation_analysis/correlation_analysis_20260601_144050.xlsx
```

当前数据统计：

```text
量表被试：37 人
VR 被试：37 人
匹配成功：37 人
有效 VR 日志：133 个
九宫格日志：74 个
四宫格日志：59 个
续存文件继承归类：15 个
unknown 日志：已剔除
```

主要输出文件：

```text
outputs/correlation_analysis/scale_scores.csv
outputs/correlation_analysis/vr_features.csv
outputs/correlation_analysis/log_manifest.csv
outputs/correlation_analysis/merged_dataset.csv
outputs/correlation_analysis/correlations.csv
outputs/correlation_analysis/correlations_reliable_n10.csv
```

## 4. 数据结构理解

VR 数据：

```text
exe_release_20260415/log/
  ATH010001VR/
    九宫格20260429160051_log_1.log
    四宫格20260429155013_log_1.log
    四宫格20260429155844_log_2.log
```

量表数据：

```text
MMSE_MoCA/
  _____ATHENA010001_____.xlsx
```

被试 ID 会统一：

```text
ATH010001VR                  -> ATH010001
_____ATHENA010001_____.xlsx  -> ATH010001
```

## 5. 四宫格和九宫格含义

四宫格 / 田字格：

```text
相对简单的 VR 社区接客任务
特征前缀：grid4_
```

九宫格：

```text
相对复杂的 VR 社区接客任务
特征前缀：grid9_
```

总体：

```text
四宫格和九宫格有效数据合并后的总体表现
特征前缀：overall_
```

续存文件规则：

```text
_log_1、_log_2、_log_3 不是独立任务，而是续存日志。
脚本会按时间顺序读取；如果 _log_2 没有任务配置，就继承前一个已知任务类型。
同一被试同一任务类型的日志会合并后再提取特征。
```

## 6. 已有脚本

### 6.1 相关性分析脚本

```text
scripts/analyze_vr_scale_correlation.py
```

作用：

- 读取 VR 日志
- 读取量表 Excel
- 匹配被试
- 识别四宫格/九宫格
- 合并续存日志
- 提取行为特征
- 计算相关性
- 输出 CSV 和 Excel

运行方式：

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\analyze_vr_scale_correlation.py
```

### 6.2 模型训练草稿

```text
scripts/train_cognitive_model.py
```

状态：

```text
草稿，未正式验证。
```

计划用途：

```text
训练 MoCA < 26 的认知风险小模型。
```

## 7. 三人分工

### A：后端数据处理负责人

A 负责：

- VR 日志解析
- 四宫格 / 九宫格识别
- 续存日志合并
- 空日志剔除
- 量表 Excel 读取
- 被试 ID 匹配
- VR 行为特征提取
- 数据相关 API

A 主要负责文件：

```text
backend/api/data_api.py
backend/services/log_parser.py
backend/services/scale_loader.py
backend/services/feature_extractor.py
backend/services/dataset_builder.py
scripts/analyze_vr_scale_correlation.py
```

A 负责接口：

```text
POST /api/data/analyze
GET  /api/data/summary
GET  /api/data/log-manifest
GET  /api/data/features
GET  /api/subjects
```

### B：后端算法模型负责人

B 负责：

- 相关性分析
- 特征筛选
- MoCA < 26 风险标签构建
- 小样本模型训练
- 留一法交叉验证
- 模型指标计算
- 个体风险预测
- 关键异常指标解释

B 主要负责文件：

```text
backend/api/model_api.py
backend/api/report_api.py
backend/services/correlation.py
backend/services/model_trainer.py
backend/services/predictor.py
backend/services/risk_scoring.py
scripts/train_cognitive_model.py
```

B 负责接口：

```text
GET  /api/correlation
POST /api/model/train
GET  /api/model/metrics
GET  /api/model/features
GET  /api/subjects/{subject_id}/risk
GET  /api/reports/{subject_id}
```

### C：前端与系统集成负责人

C 负责：

- 前端项目搭建
- mock JSON 数据
- 数据导入页
- 数据概览页
- 日志归类页
- 相关性分析页
- 模型评估页
- 个体评估页
- 报告导出入口
- 与 A/B 后端接口联调

C 主要负责文件：

```text
frontend/src/pages/
frontend/src/components/
frontend/src/api/
frontend/src/mock/
frontend/package.json
frontend/README.md
```

## 8. GitHub Desktop 协作方式

每个人使用自己的分支：

```text
A：feature/data-backend
B：feature/model-backend
C：feature/frontend-ui
```

每天开始开发前：

```text
1. 打开 GitHub Desktop
2. 切换到自己的分支
3. 点击 Fetch origin
4. 确认本地是最新状态
5. 再开始开发
```

提交规则：

```text
不要直接在 main 分支开发
只提交自己负责的文件
小功能完成后及时 commit
push 后通过 Pull Request 合并
接口字段变化必须提前通知另外两人
```

提交信息示例：

```text
A: add log parser and subject matching
B: add moca risk model metrics
C: add subject detail page mock layout
```

## 9. 前后端并行开发方式

C 不需要等 A/B 完成后端。

正确方式：

```text
先约定接口 JSON
前端用 mock JSON 做页面
A/B 后端按约定接口返回真实数据
最后把 mock 换成真实接口
```

前端 mock 文件建议：

```text
frontend/src/mock/summary.json
frontend/src/mock/subjects.json
frontend/src/mock/subject_detail.json
frontend/src/mock/correlation.json
frontend/src/mock/model_metrics.json
```

## 10. 借鉴 HTML 报告的算法执行口径

项目目录中的 `不含EEG_认知评估分析报告.html` 提供了一个可借鉴的分析模板。该报告包含基本信息、眼动、VR 与量表的综合分析；本项目当前主要使用 VR 日志和量表，因此只借鉴它的方法框架，不直接照搬其中的数据结论。

### 10.1 可借鉴的方法

```text
样本筛选
  -> 单维度相关分析
  -> 双维度组合分析
  -> 小样本模型训练
  -> 留一法交叉验证
  -> 个体解释报告
```

### 10.2 对应到本项目

```text
样本筛选：
  保留 VR 和量表都能匹配的被试，剔除空日志。

单维度相关：
  每个 grid4_*、grid9_*、overall_* 指标分别与 MMSE、MoCA、CDR、HIS 计算 Pearson 和 Spearman。

双维度组合：
  每次选择两个 VR 指标，建立 量表得分 ~ 指标A + 指标B 的线性模型。

小样本模型：
  优先使用 Ridge 或 Logistic Regression，不建议直接使用复杂深度学习。

模型验证：
  使用 LOOCV 留一法交叉验证，避免只看训练集结果。

结果解释：
  相关显著不代表因果，模型输出应解释为探索性风险评估。
```

### 10.3 B 成员后续算法任务

B 成员在模型模块中应优先实现：

```text
1. 单维度相关 Top 指标
2. 双维度组合 Top 指标
3. MoCA < 26 风险标签
4. Logistic Regression with L2 或 Ridge 小模型
5. LOOCV 留一法验证
6. 模型指标：AUC、Accuracy、Sensitivity、Specificity、F1
7. 个体风险概率和关键异常指标解释
```

双维度组合示例：

```text
MoCA ~ grid4_wrong_pickup_rate + grid9_stop_ratio
MoCA ~ grid4_map_ratio + overall_success_rate
CDR_SB ~ grid4_count_ep_timeout + overall_success_rate
```

### 10.4 C 成员前端展示建议

C 成员在前端页面中应增加：

```text
指标解释页
单维度相关 Top 指标页
双维度组合分析页
模型评估页
个体风险解释页
```

前端展示时不要只显示英文列名，应同时展示中文含义，例如：

```text
grid4_map_ratio
中文名：四宫格地图查看时间占比
解释：反映被试在简单社区任务中对辅助导航信息的依赖程度。
```

## 11. 第一批接口约定

### 数据概览

```text
GET /api/data/summary
```

```json
{
  "subject_count": 37,
  "matched_count": 37,
  "grid4_log_count": 59,
  "grid9_log_count": 74,
  "excluded_log_count": 2
}
```

### 被试列表

```text
GET /api/subjects
```

```json
[
  {
    "subject_id": "ATH010001",
    "MMSE": 25,
    "MOCA": 25,
    "CDR_global": 0.5,
    "CDR_SB": 1,
    "HIS": 1,
    "risk_probability": 0.72,
    "risk_level": "中风险"
  }
]
```

### 个体详情

```text
GET /api/subjects/ATH010001
```

```json
{
  "subject_id": "ATH010001",
  "scale_scores": {
    "MMSE": 25,
    "MOCA": 25,
    "CDR_global": 0.5,
    "CDR_SB": 1,
    "HIS": 1
  },
  "vr_summary": {
    "grid4_success_rate": 0.8,
    "grid9_success_rate": 0.6,
    "grid4_wrong_pickup_rate": 0.1,
    "grid9_wrong_pickup_rate": 0.2,
    "grid4_map_ratio": 0.15,
    "grid9_map_ratio": 0.28
  },
  "risk": {
    "probability": 0.72,
    "score": 72,
    "level": "中高风险"
  },
  "explanations": [
    "九宫格成功率低于样本均值",
    "错误接客率较高",
    "地图查看时间占比较高"
  ]
}
```

### 相关性结果

```text
GET /api/correlation
```

```json
[
  {
    "target": "MOCA",
    "feature": "grid4_wrong_pickup_rate",
    "feature_label": "四宫格错误接客率",
    "n": 21,
    "pearson_r": -0.576,
    "spearman_r": -0.354
  }
]
```

### 模型指标

```text
GET /api/model/metrics
```

```json
{
  "auc": 0.78,
  "accuracy": 0.73,
  "sensitivity": 0.80,
  "specificity": 0.65,
  "f1": 0.76
}
```

## 12. 新设备初始化步骤

1. 安装 GitHub Desktop。
2. 登录 GitHub 账号。
3. 克隆项目仓库。
4. 切换或创建自己的分支：

```text
A -> feature/data-backend
B -> feature/model-backend
C -> feature/frontend-ui
```

5. 先阅读：

```text
PROJECT_ONBOARDING.md
README.md
team_workflow_github_desktop.html
project_sync_manifest.json
```

6. 按自己的角色开始开发。

## 13. 不能忘记的事

- 当前可靠成果是数据清洗、特征提取、量表匹配和相关性分析。
- 模型训练还没正式完成。
- HTML 报告中的方法可借鉴，但其中具体样本数、眼动指标和统计结论不能直接当作本项目结果。
- 前端应先用 mock JSON 开发。
- A/B 后端应按接口约定返回 JSON。
- 不要直接改别人的核心文件。
- 接口字段改动必须同步全组。
- 不要直接在 `main` 分支开发。

