# 基于 VR 接客任务的认知评估系统

本项目用于探索被试在虚拟现实（VR）社区接客任务中的行为表现与传统认知量表之间的关系，并进一步构建一个辅助认知评估系统。

当前阶段重点完成：

- 解析 VR 行为日志
- 识别四宫格、九宫格任务
- 合并同一任务的续存日志
- 提取被试级 VR 行为特征
- 匹配 MMSE、MoCA、CDR、HIS 等量表结果
- 计算 VR 行为指标与量表分数之间的相关性

## 1. 系统目标

本系统的目标是：

> 基于被试在 VR 社区接客任务中的行为数据，提取能够反映空间导航、任务执行、注意控制和驾驶稳定性的行为特征，并与传统认知量表建立关联，最终形成认知风险评估模型和个体化解释报告。

系统未来可以输出：

- 认知风险评分
- MoCA / MMSE 风险预测
- CDR 风险倾向
- 四宫格与九宫格任务表现对比
- 关键异常行为解释

## 2. 数据结构

当前项目目录主要包括：

```text
exe_release_20260415/
  log/
    ATH010001VR/
      九宫格..._log_1.log
      四宫格..._log_1.log
      四宫格..._log_2.log
    ATH010002VR/
      ...

MMSE_MoCA/
  _____ATHENA010001_____.xlsx
  _____ATHENA010002_____.xlsx
  ...
```

其中：

- `exe_release_20260415/log` 存放 VR 行为日志
- 每个被试对应一个文件夹，例如 `ATH010001VR`
- `MMSE_MoCA` 存放量表 Excel 文件
- 每个量表文件对应一个被试，例如 `_____ATHENA010001_____.xlsx`

被试编号会自动标准化：

```text
ATH010001VR              -> ATH010001
_____ATHENA010001_____.xlsx -> ATH010001
```

## 3. 四宫格与九宫格任务理解

VR 任务包括两类社区接客场景：

- 四宫格 / 田字格：较简单的社区结构
- 九宫格：较复杂的社区结构

两类任务本质上都是在 VR 社区中开车接客，但空间复杂度不同。

因此当前分析会分别生成：

```text
grid4_*     四宫格任务特征
grid9_*     九宫格任务特征
overall_*   所有有效 VR 任务的总体特征
```

## 4. 续存日志处理

部分日志文件名中包含 `_log_1`、`_log_2` 等编号。

这些文件不是独立任务，而是同一次任务过程中因文件大小或存储机制产生的续存日志。

当前脚本的处理方式是：

1. 按日志时间顺序读取文件
2. 优先根据文件名判断四宫格或九宫格
3. 如果文件名无法判断，则读取日志内部实验配置
4. 如果续存文件内部没有实验配置，则继承前一个已知任务类型
5. 同一被试、同一任务类型的日志合并后再提取特征

无法识别且为空的日志会被剔除，不进入特征计算。

## 5. 已提取的 VR 行为特征

当前已提取的特征主要包括以下几类。

任务表现类：

```text
success_rate
count_ep_success
count_ep_fail
count_ep_timeout
count_pickup_ok
count_pickup_wrong
wrong_pickup_rate
```

时间效率类：

```text
duration
episode_duration_mean
episode_duration_std
success_time_mean
fail_time_mean
```

导航与地图类：

```text
count_map_on
map_view_duration
map_count_per_min
map_ratio
path_distance
count_zone_enter
count_zone_exit
```

驾驶控制类：

```text
speed_mean
speed_std
speed_max
stationary_ratio
count_brake_on
brake_count_per_min
throttle_mean
abs_steer_mean
abs_steer_std
```

注意与停车类：

```text
count_att_start
count_att_reset
count_stop_start
stop_duration
stop_ratio
```

## 6. 量表数据

当前读取的量表包括：

```text
MMSE
MOCA
HIS
CDR_global
CDR_SB
```

其中：

- MMSE：简易精神状态检查量表
- MoCA：蒙特利尔认知评估量表
- CDR：临床痴呆评定
- HIS：Hachinski 缺血评分

## 7. 当前已实现脚本

### 7.1 相关性分析脚本

脚本路径：

```text
scripts/analyze_vr_scale_correlation.py
```

运行方式：

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\analyze_vr_scale_correlation.py
```

输出目录：

```text
outputs/correlation_analysis/
```

主要输出文件：

```text
scale_scores.csv
vr_features.csv
log_manifest.csv
merged_dataset.csv
correlations.csv
correlations_reliable_n10.csv
correlation_analysis_*.xlsx
```

其中：

- `scale_scores.csv`：每名被试的量表分数
- `vr_features.csv`：每名被试的 VR 行为特征
- `log_manifest.csv`：每个原始日志文件的任务归类结果
- `merged_dataset.csv`：VR 特征与量表合并后的总表
- `correlations.csv`：所有相关性结果
- `correlations_reliable_n10.csv`：有效样本数不少于 10 的相关性结果
- `correlation_analysis_*.xlsx`：上述结果的 Excel 汇总版本

## 8. 当前分析结果概况

当前有效数据：

```text
量表被试：37 人
VR 被试：37 人
匹配成功：37 人
有效 VR 日志：133 个
九宫格日志：74 个
四宫格日志：59 个
```

初步结果显示，VR 行为数据中较有价值的认知相关信号主要来自：

- 任务成功率
- 超时次数
- 错误接客率
- 路径距离
- 地图查看占比
- 停车比例
- 速度与驾驶控制稳定性

其中：

- MMSE 相关指标更偏向路径距离、地图占比、完成时间波动
- MoCA 相关指标更偏向错误接客率、速度、地图依赖
- CDR 相关指标更偏向任务成功率、超时和正确接客次数
- HIS 相关指标更偏向九宫格停车比例和失败时间波动

## 9. 后续建模思路

相关性分析不是最终模型，而是模型训练前的特征筛选和解释依据。

推荐后续按以下路线实现认知评估模型：

```text
VR日志
  -> 行为特征提取
  -> 量表匹配
  -> 相关性分析
  -> 候选特征筛选
  -> 小样本模型训练
  -> 个体风险预测
  -> 解释报告生成
```

第一版建议训练小模型：

```text
目标：预测 MoCA < 26
模型：逻辑回归 / Ridge / Lasso
验证：留一法交叉验证
输出：认知风险概率
```

原因：

- 当前样本量较小，只有 37 人
- MoCA 对轻度认知下降较敏感
- 小模型更容易解释，也更适合课题展示

## 10. 系统最终形态

## 10. 借鉴 HTML 报告的算法路线

项目目录中的 `不含EEG_认知评估分析报告.html` 提供了一套可借鉴的认知评估分析框架。该报告中的具体样本数、眼动指标和统计结论不直接用于本项目，但其分析方法可以迁移到当前 VR 认知评估系统中。

推荐借鉴的流程如下：

```text
1. 样本筛选
   - 保留 VR 日志和量表都能匹配的被试
   - 剔除空日志和无效日志
   - 明确四宫格、九宫格和总体特征

2. 单维度相关分析
   - 每个 VR 指标分别与 MMSE、MoCA、CDR、HIS 做相关
   - 同时计算 Pearson 和 Spearman
   - 优先使用 Spearman 排序，因为它更适合小样本和非正态数据

3. 双维度组合分析
   - 每次选两个 VR 指标建立线性模型
   - 形式：量表得分 ~ 指标A + 指标B
   - 输出 R、R²、调整 R² 和整体检验结果

4. 小样本模型训练
   - 优先使用 Ridge / Logistic Regression 等小模型
   - 使用 LOOCV 留一法交叉验证
   - 暂不使用复杂深度学习模型

5. 个体解释报告
   - 不只输出风险概率
   - 还要输出关键异常行为指标和对应认知含义
```

在当前项目中，建议第一版模型目标为：

```text
预测 MoCA < 26 的认知风险
```

推荐模型：

```text
Logistic Regression with L2
Ridge Regression
LOOCV 留一法交叉验证
```

推荐新增的组合分析示例：

```text
MoCA ~ grid4_wrong_pickup_rate + grid9_stop_ratio
MoCA ~ grid4_map_ratio + overall_success_rate
CDR_SB ~ grid4_count_ep_timeout + overall_success_rate
```

解释口径：

```text
相关性用于筛选候选指标，不代表因果。
双维度组合用于判断两个指标合起来的解释力。
留一法模型用于评估小样本下的泛化能力。
模型结果在样本量扩大前应作为探索性结果。
```

## 11. 系统最终形态

完整系统可以分为以下模块：

```text
数据导入模块
  - 读取 VR 日志
  - 读取量表文件
  - 自动匹配被试编号

特征提取模块
  - 四宫格行为特征
  - 九宫格行为特征
  - 总体行为特征
  - 后续可加入九宫格-四宫格复杂度差异特征

统计分析模块
  - 相关性分析
  - 特征筛选
  - 群体趋势分析

模型训练模块
  - MoCA 风险模型
  - MMSE 分数预测模型
  - CDR 风险模型
  - 综合认知风险模型

评估报告模块
  - 个体风险评分
  - 关键异常指标解释
  - Excel / PDF 报告导出
```

最终输出示例：

```text
被试编号：ATH010001
认知风险概率：0.72
风险等级：中高风险

主要依据：
1. 九宫格任务成功率偏低
2. 错误接客率偏高
3. 地图查看时间占比较高
4. 停车比例高于样本均值
5. 九宫格相较四宫格表现下降明显
```

## 12. 后续建议

建议下一步继续实现：

1. 增加九宫格与四宫格的复杂度差异特征
2. 增加双维度组合分析
3. 基于相关性和认知解释筛选候选特征
4. 训练第一版 MoCA 风险小模型
5. 输出每名被试的风险概率和解释性指标
6. 生成个体化评估报告
