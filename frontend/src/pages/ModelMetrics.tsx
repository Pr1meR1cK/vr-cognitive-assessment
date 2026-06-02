// 模型评估页
import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { fetchModelMetrics } from '../api';
import type { ModelMetrics as ModelMetricsType } from '../api/types';

export default function ModelMetrics() {
  const [data, setData] = useState<ModelMetricsType | null>(null);

  useEffect(() => {
    fetchModelMetrics().then(setData);
  }, []);

  if (!data) return <p>加载中...</p>;

  const metricsRadar = [
    { name: 'AUC', value: data.metrics.auc * 100 },
    { name: '准确率', value: data.metrics.accuracy * 100 },
    { name: '敏感度', value: data.metrics.sensitivity * 100 },
    { name: '特异度', value: data.metrics.specificity * 100 },
    { name: 'F1', value: data.metrics.f1 * 100 },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>🧠 模型评估</h1>
        <p>
          {data.model_name} | 目标：{data.target} | {data.cv_method}
        </p>
      </div>

      {/* 模型指标雷达图 */}
      <div className="two-col">
        <div className="card">
          <div className="card-title">📊 模型指标（%）</div>
          <div style={{ height: 320 }}>
            <ResponsiveContainer>
              <RadarChart data={metricsRadar}>
                <PolarGrid />
                <PolarAngleAxis dataKey="name" fontSize={13} />
                <PolarRadiusAxis domain={[0, 100]} fontSize={10} />
                <Radar
                  name="模型指标"
                  dataKey="value"
                  stroke="var(--color-primary)"
                  fill="var(--color-primary)"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 特征权重 */}
        <div className="card">
          <div className="card-title">⚖️ 特征权重（Coefficient）</div>
          <div style={{ height: 320 }}>
            <ResponsiveContainer>
              <BarChart
                data={data.feature_importance}
                layout="vertical"
                margin={{ left: 120 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="label"
                  fontSize={11}
                  width={110}
                />
                <Tooltip
                  formatter={(value: number) => [value.toFixed(2), '系数']}
                />
                <Bar
                  dataKey="coefficient"
                  fill="var(--color-primary)"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 训练信息卡片 */}
      <div className="card">
        <div className="card-title">📋 训练详情</div>
        <div className="stat-grid" style={{ marginBottom: 0 }}>
          <div className="stat-item">
            <div className="stat-value">{data.sample_size}</div>
            <div className="stat-label">训练样本数</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.metrics.auc.toFixed(2)}</div>
            <div className="stat-label">AUC</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.metrics.f1.toFixed(2)}</div>
            <div className="stat-label">F1 Score</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.selected_features.length}</div>
            <div className="stat-label">入选特征数</div>
          </div>
        </div>
      </div>
    </div>
  );
}
