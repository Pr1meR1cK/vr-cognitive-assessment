// 数据概览页
import { useEffect, useState } from 'react';
import { fetchSummary } from '../api';
import type { DataSummary } from '../api/types';

export default function Dashboard() {
  const [data, setData] = useState<DataSummary | null>(null);

  useEffect(() => {
    fetchSummary().then(setData);
  }, []);

  if (!data) return <p>加载中...</p>;

  const stats = [
    { value: data.subject_count, label: '量表被试（人）' },
    { value: data.matched_count, label: 'VR 匹配成功（人）' },
    { value: data.grid4_log_count, label: '四宫格日志' },
    { value: data.grid9_log_count, label: '九宫格日志' },
    { value: data.excluded_log_count, label: '已剔除空日志' },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>📊 数据概览</h1>
        <p>当前数据集整体统计</p>
      </div>

      <div className="stat-grid">
        {stats.map((s) => (
          <div className="stat-item" key={s.label}>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">系统流程</div>
        <p style={{ fontSize: 14, color: 'var(--color-muted)' }}>
          VR 日志 + 量表 Excel → 数据清洗与被试匹配 → 四宫格/九宫格任务识别 →
          行为特征提取 → 相关性分析 → 风险模型训练 → Web 页面展示 → 个体报告导出
        </p>
      </div>
    </div>
  );
}
