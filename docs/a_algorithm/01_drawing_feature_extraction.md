# 01 — 笔迹特征提取算法

> 来源：`extract_drawing_features.py`  
> 输入：MMSE_MoCA XLSX 文件的「绘图数据」sheet（JSON 格式手写笔迹数据）  
> 输出：92 维笔迹特征（mmse_shape 22 维 + moca_trail 22 维 + moca_cube 23 维 + moca_clock 25 维）  
> 涉及任务：MMSE 图形复制、MoCA 连线测验、MoCA 复制立方体、MoCA 绘制钟表

---

## 1. 通用运动学特征（17 维，所有 4 个任务共享）

### 1.1 基础计数

| 特征 | 算法 | 公式/逻辑 |
|------|------|-----------|
| `point_count` | 统计所有笔画中的点数 | `N = Σ_i len(stroke_i)` |
| `stroke_count` | 统计笔画总数 | `len(strokes)` |

### 1.2 路径长度 — 累积欧几里得距离

```
path_length = Σ_s Σ_{i=1}^{n_s-1} √[(x_i-x_{i-1})² + (y_i-y_{i-1})²]
```

逐点累加相邻点之间的欧几里得距离，不分笔画。

### 1.3 边界框分析

| 特征 | 算法 |
|------|------|
| `bbox_width` | `max(x) - min(x)` |
| `bbox_height` | `max(y) - min(y)` |
| `bbox_area` | `bbox_width × bbox_height` |
| `bbox_aspect_ratio` | `max(w, h) / min(w, h)` |

### 1.4 速度统计

对每个笔画的相邻点对计算**瞬时速度**：`v = √(dx² + dy²) / dt`，仅在 `dt > 0.001s` 时计入。然后计算全体速度值的 `mean` 和 `std`。

### 1.5 暂停检测 — 时间阈值法

当相邻点之间的 `dt > 1.0s` 时，计为一次暂停。`pause_total_duration = Σ(dt - 1.0)`（超出阈值的部分），`pause_ratio = pause_total / total_duration`。

### 1.6 线宽统计

直接从 `lineWidth` 字段计算 `mean` 和 `std`。

### 1.7 网格占用率

将绘图区域（由 bbox 界定）划分为 20×20 等分网格，统计有点落入的格子数占比：`grid_occ = occupied_cells / 400`。

### 1.8 空间熵 — 2D 直方图 + Shannon 熵

```
H_spatial = -Σ p_i · ln(p_i + ε)
```

其中 `p_i` 是 20×20 二维直方图中每个 bin 的概率密度。熵值越高表示点分布越分散。

---

## 2. MMSE 图形复制专属特征（5 维）

### 2.1 封闭环检测

对每个笔画，如果 `首尾距离 < 0.15 × 该笔画路径长度`，判定为闭合环。

### 2.2 拐角与急转弯检测

计算连续点对的方向角序列，当相邻方向角变化超过阈值时计数：

| 特征 | 阈值 |
|------|------|
| `corner_count` | > 60° |
| `sharp_turn_count` | > 120° |

### 2.3 线段交叉计数 — 叉积法

对每对不同笔画的采样线段，使用 **叉积方向判断法** 检测是否相交：

```
d1 = cross(p3, p4, p1)    d2 = cross(p3, p4, p2)
d3 = cross(p1, p2, p3)    d4 = cross(p1, p2, p4)

相交条件: (d1*d2 < 0) AND (d3*d4 < 0)
```

采样步长为 3 个点，避免检查过多冗余线段。

### 2.4 对称性评分 — Bhattacharyya 系数

以 bbox 垂直中线 `x_mid` 为轴，将左半部分点与右半部分的镜像点合并，比较**全图像素分布**与**镜面对称分布**的相似度：

```
BC = Σ_i √(hist_full_i · hist_sym_i + ε)
```

使用 20-bin 直方图，BC ∈ [0, 1]，1 表示完美对称。

---

## 3. MoCA 连线测验专属特征（5 维）

### 3.1 路径效率

```
path_efficiency = straight_line_distance(start, end) / total_path_length
```

### 3.2 方向变化计数

与拐角检测类似，阈值 45°。

### 3.3 回溯比例

识别与整体运动方向（从起点到终点的单位向量）**反向**（投影 `proj < -0.3`）的线段，回溯距离占总路径长度的比例。

### 3.4 直线段计数 — Ramer-Douglas-Peucker（简化版）

对每个笔画进行点简化：保留方向变化超过 15° 的拐点，移除直线上的冗余中间点。简化后的点数 - 1 即为直线段数。

### 3.5 交叉计数

同 2.3 的叉积法。

---

## 4. MoCA 复制立方体专属特征（6 维）

### 4.1 拐角检测

同 2.2（> 60° 阈值）。

### 4.2 直线段计数

RDP 简化（同 3.4）。

### 4.3 平行度评分 — 方向聚类法

每隔 5 个点采样一次局部方向角（归一化到 `[0, π)`），统计所有方向角对中差值 < 15° 的比例：

```
parallel_score = parallel_pairs / total_pairs
```

### 4.4 角度一致性

方向角序列的标准差（越小越一致）。

### 4.5 交叉计数

同 2.3。

### 4.6 对称性评分

同 2.4（Bhattacharyya 系数）。

---

## 5. MoCA 绘制钟表专属特征（8 维）

### 5.1 圆度 — 半径变异系数倒数

```
circle_roundness = 1 / (1 + σ_radius / μ_radius)
```

越接近 1 表示圆越规整。

### 5.2 闭合误差

将所有点到 bbox 中心的角度排序，找**最大角度间隙**。间隙越大说明圆未闭合。

### 5.3 中心偏移 — 半径的变异系数

```
center_offset = σ_radius / μ_radius
```

### 5.4 数字区域覆盖度

将画布按角度分成 12 个扇区（模拟钟面数字位置），统计有点落入的扇区比例。

### 5.5 数字分布均匀性

计算 12 扇区的 Shannon 熵除以最大可能熵（`ln 12`），衡量数字分布是否均匀。

### 5.6 径向分布熵

对半径做 10-bin 直方图，计算 Shannon 熵，衡量数字在径向上的分布。

### 5.7 指针数量估计

从 bbox 中心出发、路径长度 > `bbox_width × 0.2` 的笔画被视为"指针"。统计满足条件的笔画数。

### 5.8 指针角度特征

取最长的两个"指针"，计算两者角度差的度数。

---

## 算法分类速查

| 算法类别 | 具体方法 | 应用特征 |
|----------|----------|----------|
| 距离/路径计算 | 欧几里得距离累积 | path_length, path_efficiency, backtrack_ratio |
| 方向分析 | atan2 方向角 + 角差检测 | corner_count, sharp_turn_count, direction_change_count, angle_consistency |
| 交叉检测 | 叉积方向判断法 | intersection_count, crossing_count |
| 点简化 | Ramer-Douglas-Peucker（简化版） | segment_count, line_segment_count |
| 对称性 | Bhattacharyya 系数（直方图比较） | symmetry_score |
| 聚类分析 | 方向角聚类（成对比较） | parallel_score |
| 熵分析 | 2D 直方图 + Shannon 熵 | spatial_entropy, number_distribution_balance, radial_distribution_entropy |
| 圆分析 | 半径变异系数 + 角度间隙 | circle_roundness, circle_closure_error, center_offset |
| 扇区分析 | 角度分箱 | number_region_coverage |
| 指针估计 | 距离阈值 + 路径长度 | hand_count_estimate, hand_angle_feature |
| 时间阈值 | dt > threshold 判定 | pause_count, pause_ratio, pause_total_duration |
| 封闭检测 | 首尾距离/路径长度比例 | closed_loop_count |
