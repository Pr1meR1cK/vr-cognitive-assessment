# 03 — 数据集构建算法

> 来源：`output1/build_merged_dataset.py`  
> 输入：VR 特征（grid4/grid9）、量表 Excel、笔迹特征 CSV  
> 输出：`merged_dataset.csv`（37 × 178 列）、`scale_scores.csv`、`vr_features.csv`

---

## 1. 量表分数提取

### 1.1 Excel 解析

从 `MMSE_MoCA/*.xlsx` 的**最后一个 sheet**（量表总分）中读取：

| 行号 | B 列值 | 字段 |
|------|--------|------|
| Row 1 | 被试原始 ID（如 `_____ATHENA010001_____`） | subject_id |
| Row 4 | 数值 | MMSE |
| Row 5 | 数值 | MOCA |
| Row 6 | `global-X_SB-Y` 格式或空/"无计分" | CDR |
| Row 7 | 数值或空 | HIS |

### 1.2 被试 ID 统一化

```
输入: "_____ATHENA010001_____"
步骤1: 移除 "_____ATHENA" 和 "_____" → "010001"
步骤2: 确保 ATH 前缀 → "ATH010001"

输入: "ATH010002VR"
步骤1: 移除 "VR" → "ATH010002"
步骤2: 已有 ATH 前缀，不变 → "ATH010002"
```

### 1.3 CDR 格式解析 — 正则匹配法

```
正则: global-([\d.]+)_SB-([\d.]+)

示例:
  "global-0.5_SB-1"    → CDR_global=0.5, CDR_SB=1.0
  "global-1_SB-9"      → CDR_global=1.0, CDR_SB=9.0
  "global-0_SB-0"      → CDR_global=0.0, CDR_SB=0.0
  "无计分" / None       → CDR_global=NaN, CDR_SB=NaN   (空字符串标记)
```

### 1.4 缺失值处理

`"无计分"` 或无法解析的值统一标记为空字符串 `""`（CSV 中显示为空），与真正的 `NaN` 区分。

---

## 2. 衍生特征计算

### 2.1 总体特征 `overall_*` — 加权合并法

将同一被试的 grid4 和 grid9 合并为总体特征。核心原则：**可计数的直接求和，率/比例用原值加权平均**。

#### 计数类（合并求和）

```
total_ep_success = grid4_count_ep_success + grid9_count_ep_success
total_ep_fail    = grid4_count_ep_fail   + grid9_count_ep_fail
total_ep_timeout = grid4_count_ep_timeout + grid9_count_ep_timeout
```

#### 率/比例类（从合并计数重新计算）

```
overall_success_rate     = total_ep_success / (total_ep_success + total_ep_fail + total_ep_timeout)
overall_wrong_pickup_rate = total_pickup_wrong / (total_pickup_ok + total_pickup_wrong)
```

#### 时长类（求和）

```
overall_duration = grid4_duration + grid9_duration
```

#### 加权平均类（以各任务时长为权重）

```
overall_speed_mean = (grid4_speed_mean × grid4_duration + grid9_speed_mean × grid9_duration)
                   / (grid4_duration + grid9_duration)

overall_speed_std  = √[ (grid4_speed_std² × grid4_duration + grid9_speed_std² × grid9_duration)
                       / (grid4_duration + grid9_duration) ]
```

**原理**：时长加权确保占时间更长的任务对总体统计的贡献更大。

| overall 特征 | 方法 |
|--------------|------|
| `overall_success_rate` | 合并计数后重新计算 |
| `overall_wrong_pickup_rate` | 合并计数后重新计算 |
| `overall_duration` | 直接求和 |
| `overall_map_ratio` | 合并 map_view_duration 总和 / 总 duration |
| `overall_path_distance` | 直接求和 |
| `overall_speed_mean` | 时长加权平均 |
| `overall_speed_std` | 时长加权方差开方 |
| `overall_stationary_ratio` | 时长加权平均 |
| `overall_stop_ratio` | 合并 stop_duration 总和 / 总 duration |

---

### 2.2 复杂度差异特征 `diff_*` — 简单差值法

表达九宫格（复杂任务）相对四宫格（简单任务）的行为变化：

```
diff_success_rate       = grid9_success_rate - grid4_success_rate
diff_wrong_pickup_rate  = grid9_wrong_pickup_rate - grid4_wrong_pickup_rate
diff_map_ratio          = grid9_map_ratio - grid4_map_ratio
diff_stop_ratio         = grid9_stop_ratio - grid4_stop_ratio
diff_path_distance      = grid9_path_distance - grid4_path_distance
```

**认知含义**：

| 正值表示 | 负值表示 |
|----------|----------|
| 复杂任务成功率更高（认知储备好） | 复杂任务成功率下降（复杂度敏感） |
| 复杂任务错误接客更多（判别力下降） | 复杂任务错误接客更少 |
| 复杂任务更依赖地图（策略调整） | 复杂任务地图使用减少 |
| 复杂任务停车更多/路径更长 | 复杂任务停车更少/路径更短 |

---

## 3. 宽表拼接

### 3.1 列顺序

```
subject_id
├── [量表] MMSE, MOCA, CDR_global, CDR_SB, HIS          (5 列)
├── [grid4] grid4_success_rate, ...grid4_stop_ratio       (33 列)
├── [grid9] grid9_success_rate, ...grid9_stop_ratio       (33 列)
├── [overall] overall_success_rate, ...overall_stop_ratio (9 列)
├── [diff] diff_success_rate, ...diff_path_distance       (5 列)
└── [drawing] drawing_mmse_shape_bbox_area, ...           (92 列)
─────────────────────────────────────────────────────────────
总计: 178 列
```

### 3.2 多源合并 — 全外连接

以所有出现过的 `subject_id` 并集为行索引，每个数据源按其 `subject_id` 填入对应列。缺失数据留空（`""`）。

```
all_subjects = sorted(set(VR_ids ∪ scale_ids ∪ drawing_ids))

for sid in all_subjects:
    从 vr_data[sid] 填 grid4/grid9 列
    从 scale_data[sid] 填量表列
    从 drawing_data[sid] 填笔迹列
    计算 overall 和 diff 列
```

### 3.3 缺失值处理

| 场景 | 处理 |
|------|------|
| 被试无 VR 数据 | grid4/grid9/overall/diff 列全空 |
| 被试无量表数据 | MMSE/MOCA/CDR/HIS 列全空 |
| 被试无笔迹数据 | drawing_* 列全空（如 ATH010001） |
| 被试无 grid4 | grid4 列空，diff 列也空（因为依赖 grid4） |
| CDR 为 "无计分" | CDR_global 和 CDR_SB 为空字符串 |
| NaN 值 | 统一转为空字符串再写入 CSV |

---

## 4. 算法分类速查

| 类别 | 方法 | 应用 |
|------|------|------|
| 正则解析 | `global-([\d.]+)_SB-([\d.]+)` | CDR 格式解析 |
| 字符串清洗 | 移除前缀/后缀，统一前缀 | subject_id 统一化 |
| 加权平均 | 以时长为权重的加权均值 | overall speed, stationary |
| 方差传播 | 加权方差开方 | overall speed_std |
| 直接求和 | 跨任务计数累加 | overall duration, path_distance |
| 差值计算 | 任务间减法 | diff_* 复杂度差异 |
| 集合运算 | 所有源的 subject_id 并集 | 全外连接 |
| 空值处理 | NaN → "" 空字符串 | CSV 写入 |

---

## 5. 完整数据流

```
┌─────────────────┐
│ VR 日志 (.log)   │──→ 日志解析 ──→ 事件匹配 ──→ grid4_* (33 维)
│ (37 subjects)   │                            grid9_* (33 维)
└─────────────────┘                                     │
                                                        ├──→ overall_* (9 维，加权合并)
┌─────────────────┐                                     │
│ 量表 Excel       │──→ sheet 读取 ──→ CDR 解析 ──→ MMSE, MOCA,     │
│ (37 subjects)   │                     ID 统一化     CDR_gl, CDR_SB, │
└─────────────────┘                                  HIS (5 维)       │
                                                                      ├──→ merged_dataset.csv
┌─────────────────┐                                                  │    (37 rows × 178 cols)
│ 绘图 JSON        │──→ 点序列解析 ──→ 通用特征 ──→ drawing_* (92 维) │
│ (37 subjects)   │                  专属特征                         │
└─────────────────┘                                                  │
                                              ┌───────────────────────┘
                                              │ diff_* (5 维，简单差值)
                                              │ grid9_* - grid4_*
                                              └───────────────────────
```
