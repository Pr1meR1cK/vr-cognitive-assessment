// 相关性分析页
import { useEffect, useState } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { fetchCorrelation } from '../api';
import type { CorrelationItem } from '../api/types';

const TARGET_COLORS: Record<string, string> = {
  MMSE: '#1f6feb',
  MOCA: '#1a7f37',
  CDR_global: '#b65c00',
  HIS: '#b42318',
};

export default function Correlation() {
  const [data, setData] = useState<CorrelationItem[]>([]);

  useEffect(() => {
    fetchCorrelation().then(setData);
  }, []);

  // 散点图数据：x=pearson_r, y=feature
  const scatterData = data
    .filter((d) => d.significant)
    .map((d) => ({
      x: d.pearson_r,
      y: d.feature_label,
      z: Math.abs(d.pearson_r) * 100,
      target: d.target,
      n: d.n,
      p: d.p_value,
    }));

  return (
    <div>
      <div className="page-header">
        <h1>🔗 相关性分析</h1>
        <p>VR 行为指标 vs 传统量表分数（仅显示显著相关 p &lt; 0.05）</p>
      </div>

      {/* 显著相关散点图 */}
      <div className="card">
        <div className="card-title">📈 显著相关特征（Pearson r）</div>
        <div style={{ height: scatterData.length * 36 + 60, minHeight: 250 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
            <ScatterChart
              margin={{ top: 10, right: 30, bottom: 10, left: 160 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="x"
                name="Pearson r"
                domain={[-1, 1]}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                type="category"
                dataKey="y"
                width={150}
                tick={{ fontSize: 12 }}
              />
              <ZAxis type="number" dataKey="z" range={[40, 120]} />
              <Tooltip
                formatter={(value: unknown, name: unknown) => {
                  const label = String(name);
                  const numericValue = Number(value ?? 0);
                  if (label === 'Pearson r') return [numericValue.toFixed(3), label];
                  return [String(value ?? ''), label];
                }}
                content={({ payload }) => {
                  if (!payload || payload.length === 0) return null;
                  const p = payload[0].payload;
                  return (
                    <div
                      style={{
                        background: '#fff',
                        border: '1px solid #d9e0e7',
                        borderRadius: 6,
                        padding: '8px 12px',
                        fontSize: 13,
                      }}
                    >
                      <div><strong>{p.y}</strong></div>
                      <div>量表: {p.target} | r = {p.x.toFixed(3)}</div>
                      <div>n = {p.n} | p = {p.p.toFixed(3)}</div>
                    </div>
                  );
                }}
              />
              <Scatter data={scatterData}>
                {scatterData.map((d, i) => (
                  <Cell key={i} fill={TARGET_COLORS[d.target] || '#888'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        {/* 图例 */}
        <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 13 }}>
          {Object.entries(TARGET_COLORS).map(([k, v]) => (
            <span key={k}>
              <span
                style={{
                  display: 'inline-block',
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: v,
                  marginRight: 4,
                  verticalAlign: 'middle',
                }}
              />
              {k}
            </span>
          ))}
        </div>
      </div>

      {/* 完整相关性表格 */}
      <div className="card">
        <div className="card-title">📋 全部相关性结果</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>量表</th>
                <th>VR 指标</th>
                <th>n</th>
                <th>Pearson r</th>
                <th>Spearman ρ</th>
                <th>p 值</th>
                <th>显著性</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d, i) => (
                <tr key={i}>
                  <td><strong>{d.target}</strong></td>
                  <td>{d.feature_label}</td>
                  <td>{d.n}</td>
                  <td>{d.pearson_r.toFixed(3)}</td>
                  <td>{d.spearman_r.toFixed(3)}</td>
                  <td>{d.p_value.toFixed(3)}</td>
                  <td>
                    {d.significant ? (
                      <span className="risk-tag risk-low">显著</span>
                    ) : (
                      <span style={{ color: 'var(--color-muted)' }}>不显著</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
