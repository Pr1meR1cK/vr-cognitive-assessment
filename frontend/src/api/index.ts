// ========================================
// API 对接层
// 当前使用 mock 数据；联调时只需将 fetch 地址
// 改为真实后端接口即可，无需修改页面代码
// ========================================

import type {
  DataSummary,
  SubjectListItem,
  SubjectDetail,
  CorrelationItem,
  ModelMetrics,
} from './types';

// mock 数据导入
import mockSummary from '../mock/summary.json';
import mockSubjects from '../mock/subjects.json';
import mockSubjectDetail from '../mock/subject_detail.json';
import mockCorrelation from '../mock/correlation.json';
import mockModelMetrics from '../mock/model_metrics.json';

// 切换开关：VITE_USE_MOCK=true 时使用本地 mock；默认请求真实后端
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// 后端基础地址
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// ========================================
// 通用 fetch 封装
// ========================================
async function request<T>(path: string): Promise<T> {
  if (USE_MOCK) {
    // mock 模式：按路径返回对应假数据
    return mockResponse<T>(path);
  }
  // 真实模式
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// 简单 mock 路由
function mockResponse<T>(path: string): Promise<T> {
  // 去掉 query 参数
  const clean = path.split('?')[0];

  if (clean === '/api/data/summary') return as<T>(mockSummary);
  if (clean === '/api/subjects') return as<T>(mockSubjects);
  if (clean === '/api/correlation') return as<T>(mockCorrelation);
  if (clean === '/api/model/metrics') return as<T>(mockModelMetrics);

  // /api/subjects/ATH010001 -> 返回详情
  const subjectMatch = clean.match(/^\/api\/subjects\/(ATH\d+)$/);
  if (subjectMatch) {
    const detail = { ...mockSubjectDetail, subject_id: subjectMatch[1] } as unknown;
    return as<T>(detail);
  }

  throw new Error(`Mock 未覆盖: ${path}`);
}

function as<T>(data: unknown): Promise<T> {
  return Promise.resolve(data as T);
}

// ========================================
// 接口方法（按 PROJECT_ONBOARDING 约定）
// ========================================

/** 数据概览 */
export function fetchSummary(): Promise<DataSummary> {
  return request<DataSummary>('/api/data/summary');
}

/** 被试列表 */
export function fetchSubjects(): Promise<SubjectListItem[]> {
  return request<SubjectListItem[]>('/api/subjects');
}

/** 个体详情 */
export function fetchSubjectDetail(id: string): Promise<SubjectDetail> {
  return request<SubjectDetail>(`/api/subjects/${id}`);
}

/** 相关性结果 */
export function fetchCorrelation(): Promise<CorrelationItem[]> {
  return request<CorrelationItem[]>('/api/correlation');
}

/** 模型指标 */
export function fetchModelMetrics(): Promise<ModelMetrics> {
  return request<ModelMetrics>('/api/model/metrics');
}
