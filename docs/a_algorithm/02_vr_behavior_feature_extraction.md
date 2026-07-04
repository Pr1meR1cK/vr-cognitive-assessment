# 02 — VR 行为特征提取算法

> 来源：`output1/build_merged_dataset.py`  
> 输入：`exe_release_20260415/log/` 下每个被试文件夹内的 `.log` 文件（管道分隔的 JSON 行日志）  
> 输出：四宫格 33 维（`grid4_*`）+ 九宫格 33 维（`grid9_*`），共 66 维原始 VR 特征  
> 任务类型：四宫格（田字格社区，简单任务）、九宫格（九宫格社区，复杂任务）

---

## 1. 日志解析与事件匹配

### 1.1 行协议解析

日志格式：`relative_time|real_time|event_type|json_payload`

```
示例:
117.1806|2026-04-29 15:50:13.076764|INIT_EXP|{"COMM": {"NAME": "田字格社区"}, ...}
```

解析步骤：
1. 按 `|` 分割为 4 段
2. 第 1 段：相对时间（float，秒）
3. 第 2 段：真实时间（ISO 格式，备用）
4. 第 3 段：事件类型（字符串）
5. 第 4 段：JSON payload

### 1.2 任务类型识别 — 双通道回退策略

**策略优先级：**

```
通道1（文件名） → 通道2（INIT_EXP COMM.NAME） → 通道3（时间序继承）
```

| 通道 | 方法 | 匹配规则 |
|------|------|----------|
| 通道1 | 文件名关键词 | "四宫格"/"田字格" → grid4；"九宫格" → grid9 |
| 通道2 | 读取前 100 行中 INIT_EXP 的 `COMM.NAME` | "田字格社区" → grid4；"九宫格社区" → grid9 |
| 通道3 | 时间顺序继承 | 若文件无 INIT_EXP 配置（续存日志），继承同目录中前一个已知文件的 task_type |

### 1.3 续存日志合并

`_log_1.log`、`_log_2.log`、`_log_3.log` 等是同一次任务因文件大小而分割的续存日志。处理方式：

1. 按文件名排序所有 `.log` 文件
2. 对每类任务类型（grid4/grid9），将该类型的所有文件合并
3. 合并后的所有事件按 `rel_time` 排序
4. 特征从合并后的事件流中统一提取

### 1.4 关键事件匹配算法 — 前向配对法

多类事件需要配对：`EVENT_START → EVENT_END`。

**算法（以 MAP_ON → MAP_OFF 为例）：**

```
for each MAP_ON event (按时间排序):
    找时间上第一个 rel_time > MAP_ON.rel_time 的 MAP_OFF
    duration += MAP_OFF.rel_time - MAP_ON.rel_time
```

此算法假设事件不会嵌套（同一时刻只开一个地图/停一次车），适用于：
- `MAP_ON → MAP_OFF`（地图使用时长）
- `STOP_START → STOP_END`（停车时长）
- `EP_START → EP_SUCCESS / EP_FAIL / EP_TIMEOUT`（Episode 时长）

### 1.5 BASE_INFO 遥测数据采集

从所有 `BASE_INFO` 事件中采集如下字段用于驾驶行为分析：

| 字段 | 含义 | 用途 |
|------|------|------|
| `POS_X, POS_Y, POS_Z` | 3D 位置 | 路径距离、位置变化 |
| `SPEED` | 当前速度 | 速度统计、静止检测 |
| `THROTTLE` | 油门值 | 油门均值 |
| `BRAKE` | 刹车值 | 刹车频率 |
| `STEER_ANGLE` | 方向盘角度 | 转向行为分析 |

---

## 2. 驾驶行为分析

### 2.1 任务表现特征（7 维）

| 特征 | 算法 | 公式 |
|------|------|------|
| `count_ep_success` | 计数 EP_SUCCESS 事件 | — |
| `count_ep_fail` | 计数 EP_FAIL 事件 | — |
| `count_ep_timeout` | 计数 EP_TIMEOUT 事件 | — |
| `success_rate` | 成功次数/总次数 | `n_success / (n_success + n_fail + n_timeout)` |
| `count_pickup_ok` | 计数 PICKUP_OK 事件 | — |
| `count_pickup_wrong` | 计数 PICKUP_WRONG 事件 | — |
| `wrong_pickup_rate` | 错误接客率 | `n_wrong / (n_ok + n_wrong)` |

### 2.2 时间效率特征（5 维）

| 特征 | 算法 |
|------|------|
| `duration` | `max(BASE_INFO.rel_time) - min(BASE_INFO.rel_time)` |
| `episode_duration_mean` | 所有 EP_START→EP_END 时长的均值 |
| `episode_duration_std` | 所有 EP_START→EP_END 时长的标准差 |
| `success_time_mean` | EP_START→EP_SUCCESS 时长的均值 |
| `fail_time_mean` | EP_START→EP_FAIL/EP_TIMEOUT 时长的均值 |

### 2.3 导航与地图特征（7 维）

| 特征 | 算法 |
|------|------|
| `count_map_on` | 计数 MAP_ON 事件 |
| `map_view_duration` | MAP_ON→MAP_OFF 配对累计时长 |
| `map_count_per_min` | `count_map_on / duration × 60` |
| `map_ratio` | `map_view_duration / duration` |
| `path_distance` | 累积欧几里得距离（见 2.6） |
| `count_zone_enter` | 计数 ZONE_ENTER 事件 |
| `count_zone_exit` | 计数 ZONE_EXIT 事件 |

### 2.4 驾驶控制特征（9 维）

| 特征 | 算法 |
|------|------|
| `speed_mean` | BASE_INFO SPEED 的均值 |
| `speed_std` | BASE_INFO SPEED 的标准差 |
| `speed_max` | BASE_INFO SPEED 的最大值 |
| `stationary_ratio` | SPEED < V_STOP_THR（来自 INIT_EXP，默认 0.01）的比例 |
| `count_brake_on` | 计数 BRAKE_ON 事件 |
| `brake_count_per_min` | `count_brake_on / duration × 60` |
| `throttle_mean` | BASE_INFO THROTTLE 的均值 |
| `abs_steer_mean` | `|STEER_ANGLE|` 的均值 |
| `abs_steer_std` | `|STEER_ANGLE|` 的标准差 |

### 2.5 注意力与停车特征（5 维）

| 特征 | 算法 |
|------|------|
| `count_att_start` | 计数 ATT_START 事件 |
| `count_att_reset` | 计数 ATT_RESET 事件 |
| `count_stop_start` | 计数 STOP_START 事件 |
| `stop_duration` | STOP_START→STOP_END 配对累计时长 |
| `stop_ratio` | `stop_duration / duration` |

### 2.6 路径距离 — 累积 3D 欧几里得距离

```
path_distance = Σ_{i=1}^{N-1} √[(x_i-x_{i-1})² + (y_i-y_{i-1})² + (z_i-z_{i-1})²]
```

对 BASE_INFO 的连续位置采样点累加 3D 距离。与笔迹的 2D 路径长度算法相同，增加 z 轴。

---

## 3. 特征维度对照表

| VR_FIELDS（33 维） | 分类 |
|---------------------|------|
| `success_rate` | 任务表现 |
| `count_ep_success` | 任务表现 |
| `count_ep_fail` | 任务表现 |
| `count_ep_timeout` | 任务表现 |
| `count_pickup_ok` | 任务表现 |
| `count_pickup_wrong` | 任务表现 |
| `wrong_pickup_rate` | 任务表现 |
| `duration` | 时间效率 |
| `episode_duration_mean` | 时间效率 |
| `episode_duration_std` | 时间效率 |
| `success_time_mean` | 时间效率 |
| `fail_time_mean` | 时间效率 |
| `count_map_on` | 导航/地图 |
| `map_view_duration` | 导航/地图 |
| `map_count_per_min` | 导航/地图 |
| `map_ratio` | 导航/地图 |
| `path_distance` | 导航/地图 |
| `count_zone_enter` | 导航/地图 |
| `count_zone_exit` | 导航/地图 |
| `speed_mean` | 驾驶控制 |
| `speed_std` | 驾驶控制 |
| `speed_max` | 驾驶控制 |
| `stationary_ratio` | 驾驶控制 |
| `count_brake_on` | 驾驶控制 |
| `brake_count_per_min` | 驾驶控制 |
| `throttle_mean` | 驾驶控制 |
| `abs_steer_mean` | 驾驶控制 |
| `abs_steer_std` | 驾驶控制 |
| `count_att_start` | 注意力/停车 |
| `count_att_reset` | 注意力/停车 |
| `count_stop_start` | 注意力/停车 |
| `stop_duration` | 注意力/停车 |
| `stop_ratio` | 注意力/停车 |

---

## 4. 事件类型完整清单

| 事件 | 计数方式 | 用途 |
|------|----------|------|
| `INIT_EXP` | 首次出现 | 任务类型识别、参数获取（V_STOP_THR等） |
| `START_EXP` | — | 实验开始标记 |
| `EP_START` | — | Episode 起始点 |
| `EP_SUCCESS` | 计数 | 任务成功 |
| `EP_FAIL` | 计数 | 任务失败 |
| `EP_TIMEOUT` | 计数 | 任务超时 |
| `PICKUP_OK` | 计数 | 正确接客 |
| `PICKUP_WRONG` | 计数 | 错误接客 |
| `MAP_ON` | 计数 + 配对 | 打开地图 |
| `MAP_OFF` | 配对用 | 关闭地图 |
| `STOP_START` | 计数 + 配对 | 开始停车 |
| `STOP_END` | 配对用 | 结束停车 |
| `BRAKE_ON` | 计数 | 刹车激活 |
| `BRAKE_OFF` | — | 刹车释放 |
| `ATT_START` | 计数 | 注意力任务开始 |
| `ATT_RESET` | 计数 | 注意力任务重置 |
| `ZONE_ENTER` | 计数 | 进入区域 |
| `ZONE_EXIT` | 计数 | 离开区域 |
| `GATE_IN` | — | 进入门 |
| `GATE_OUT` | — | 离开门 |
| `BASE_INFO` | 全部采集 | 遥测数据（位置/速度/油门/刹车/方向盘） |
