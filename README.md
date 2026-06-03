# 基于 VR 接客任务的认知评估系统

本项目计划构建一个 Web 版认知评估系统，用于读取被试在 VR 四宫格/九宫格社区接客任务中的行为日志，并结合 MMSE、MoCA、CDR、HIS 等量表结果，完成数据处理、行为特征提取、相关性分析、风险建模、个体评估展示和报告导出。

## 当前项目状态

当前仓库状态：

```text
已具备：
- 原始 VR 日志数据
- 原始量表 Excel 数据
- 项目说明文档
- GitHub Desktop 协作说明
- 不含EEG_认知评估分析报告.html 参考报告

尚未进行：
- 后端数据处理服务
- 相关性分析程序
- 模型训练程序
- Web 前端页面
- 个体评估报告导出
```

也就是说，当前仓库可以视为“数据与项目方案已准备，算法和系统模块待实现”的状态。

## 数据结构

当前数据主要包括：

```text
exe_release_20260415/
  log/
    ATH010001VR/
      九宫格..._log_1.log
      四宫格..._log_1.log
      四宫格..._log_2.log

MMSE_MoCA/
  _____ATHENA010001_____.xlsx
  _____ATHENA010002_____.xlsx
```

被试编号需要统一，例如：

```text
ATH010001VR                  -> ATH010001
_____ATHENA010001_____.xlsx  -> ATH010001
```

## VR 任务理解

VR 任务包括两类社区接客场景：

```text
grid4_*     四宫格 / 田字格社区接客任务
grid9_*     九宫格社区接客任务
overall_*   所有有效 VR 任务的总体表现
```

四宫格相对简单，九宫格空间结构更复杂。后续分析应分别提取四宫格、九宫格和总体特征。

续存日志规则：

```text
_log_1、_log_2、_log_3 等不是独立任务，而是续存文件。
处理时应按时间顺序读取。
如果续存文件缺少任务配置，则继承前一个已知任务类型。
同一被试、同一任务类型的日志合并后再提取特征。
```

## 计划提取的 VR 特征

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

建议后续新增复杂度差异特征：

```text
diff_success_rate = grid9_success_rate - grid4_success_rate
diff_wrong_pickup_rate = grid9_wrong_pickup_rate - grid4_wrong_pickup_rate
diff_map_ratio = grid9_map_ratio - grid4_map_ratio
diff_stop_ratio = grid9_stop_ratio - grid4_stop_ratio
diff_path_distance = grid9_path_distance - grid4_path_distance
```

## 借鉴 HTML 报告的算法路线

项目目录中的 `不含EEG_认知评估分析报告.html` 提供了一套可借鉴的分析框架。该报告中的具体样本数、眼动指标和统计结论不直接用于本项目，但其分析方法可以迁移。

推荐算法流程：

```text
1. 样本筛选
2. 单维度相关分析
3. 双维度组合分析
4. 小样本模型训练
5. LOOCV 留一法交叉验证
6. 个体风险解释报告
```

具体建议：

```text
单维度相关：
  对每个 VR 指标分别计算与 MMSE、MoCA、CDR、HIS 的 Pearson 和 Spearman。
  优先用 Spearman 排序。

双维度组合：
  建立 量表得分 ~ 指标A + 指标B 的线性模型。
  输出 R、R²、调整 R² 和整体检验结果。

小样本模型：
  第一版建议预测 MoCA < 26。
  推荐 Logistic Regression with L2 或 Ridge Regression。
  使用 LOOCV 留一法交叉验证。
```

示例组合：

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

## 三人分工

A：后端数据处理负责人

```text
负责 VR 日志解析、四宫格/九宫格识别、续存日志合并、量表读取、被试 ID 匹配、行为特征提取和数据接口。
```

B：后端算法模型负责人

```text
负责相关性分析、双维度组合分析、特征筛选、MoCA 风险模型、LOOCV 验证、风险评分和模型接口。
```

C：前端与系统集成负责人

```text
负责 Web 前端、mock 数据、接口调用、图表展示、个体评估页面、报告导出入口和系统演示。
```

## 推荐页面

```text
数据导入页
数据概览页
指标解释页
日志归类页
单维度相关 Top 指标页
双维度组合分析页
模型评估页
个体风险解释页
报告导出页
```

## 下一步

```text
1. A 重新实现数据处理脚本或 FastAPI 数据服务。
2. B 重新实现相关性、双维度组合和 MoCA<26 小模型。
3. C 使用 mock JSON 并行开发前端页面。
4. 三人统一接口字段后再联调。
```
