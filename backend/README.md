# VR 认知评估系统后端

本目录提供课程设计演示用的 FastAPI 服务。后端优先读取 A/B 脚本生成的前端接口产物，并按 C 前端页面约定返回 HTTP 响应；如果本机还没有生成产物，则自动回退到 `frontend/src/mock`，便于先完成联调。

## 启动

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

服务地址：

```text
http://localhost:8000
```

健康检查：

```text
GET /api/health
```

返回中的 `data_source` 会说明当前读取的是：

```text
outputs/frontend_api_real
outputs/frontend_api_mock_full
outputs/frontend_api
frontend/src/mock
```

## 接入 A/B 产物

真实数据到位后，先按远端文档运行 B 流程：

```bash
python scripts/generate_cognitive_results.py --input outputs/cognitive_pipeline_real/merged_dataset.csv --output-dir outputs/cognitive_pipeline_real
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_real/results --output-dir outputs/frontend_api_real
```

如果只做 mock full 演示，可按 `docs/MOCK_FULL_DEMO_FLOW.md` 生成：

```bash
python scripts/build_frontend_api_payloads.py --results-dir outputs/cognitive_pipeline_mock_full/results --output-dir outputs/frontend_api_mock_full
```

然后重启后端即可。

## 已实现接口

```text
GET  /api/health
GET  /api/frontend/index
GET  /api/data/summary
GET  /api/subjects
GET  /api/subjects/{subject_id}
GET  /api/correlation
GET  /api/model/metrics
GET  /api/reports/{subject_id}
POST /api/data/analyze
```

说明：当前仓库不包含真实数据目录和生成结果目录。没有 `outputs/frontend_api*` 时，接口会回退到 mock 数据；生成产物存在时，会优先读取 A/B 产物。
