# VR 认知评估系统 — 前端

## 技术栈

| 技术 | 用途 |
|------|------|
| React 19 | UI 框架 |
| TypeScript | 类型安全 |
| Vite 8 | 构建工具 / 开发服务器 |
| React Router 7 | 页面路由 |
| Recharts 2 | 数据可视化图表 |

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

## 项目结构

```
frontend/src/
├── api/
│   ├── index.ts          # API 调用层（mock / 真实切换）
│   └── types.ts          # 所有接口类型定义
├── mock/
│   ├── summary.json      # 数据概览 mock
│   ├── subjects.json     # 被试列表 mock
│   ├── subject_detail.json # 个体详情 mock
│   ├── correlation.json  # 相关性结果 mock
│   └── model_metrics.json # 模型指标 mock
├── components/
│   └── Layout.tsx        # 全局布局（侧边栏 + 内容区）
├── pages/
│   ├── Dashboard.tsx     # 数据概览页
│   ├── Subjects.tsx      # 被试列表页
│   ├── SubjectDetail.tsx # 个体评估详情页
│   ├── Correlation.tsx   # 相关性分析页
│   ├── ModelMetrics.tsx  # 模型评估页
│   └── DataImport.tsx    # 数据导入页
├── App.tsx               # 路由配置
├── main.tsx              # 入口文件
└── index.css             # 全局样式
```

## 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | 数据概览 | 数据集整体统计卡片 |
| `/subjects` | 被试列表 | 被试表格，点击行查看详情 |
| `/subjects/:id` | 个体评估 | 雷达图 + 柱状图 + 风险解释 |
| `/correlation` | 相关性分析 | 散点图 + 完整相关系数表 |
| `/model` | 模型评估 | 指标雷达图 + 特征权重图 |
| `/import` | 数据导入 | 等待 A 实现接口 |

## Mock 数据模式

当前 `src/api/index.ts` 中 `USE_MOCK = true`，所有接口返回本地 mock 数据。

联调时只需：
1. 将 `USE_MOCK` 改为 `false`
2. 修改 `BASE_URL` 为实际后端地址
3. 无需改动任何页面代码

## 接口约定

所有接口路径和 JSON 字段与 `PROJECT_ONBOARDING.md` 保持一致。详见项目根目录文档。
