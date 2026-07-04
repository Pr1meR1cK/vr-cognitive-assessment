// 个体评估详情页
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { fetchSubjectDetail } from '../api';
import type { SubjectDetail as SubjectDetailType } from '../api/types';

function riskClass(level: string) {
  if (level.includes('高')) return 'risk-tag risk-high';
  if (level.includes('中')) return 'risk-tag risk-mid';
  return 'risk-tag risk-low';
}

export default function SubjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SubjectDetailType | null>(null);

  useEffect(() => {
    if (id) fetchSubjectDetail(id).then(setData);
  }, [id]);

  if (!data) return <p>加载中...</p>;

  // 雷达图：四宫格 vs 九宫格对比
  const radarData = [
    { name: '成功率', grid4: data.vr_summary.grid4_success_rate * 100, grid9: data.vr_summary.grid9_success_rate * 100 },
    { name: '错误接客率', grid4: data.vr_summary.grid4_wrong_pickup_rate * 100, grid9: data.vr_summary.grid9_wrong_pickup_rate * 100 },
    { name: '地图查看占比', grid4: data.vr_summary.grid4_map_ratio * 100, grid9: data.vr_summary.grid9_map_ratio * 100 },
    { name: '停车比例', grid4: data.vr_summary.grid4_stop_ratio * 100, grid9: data.vr_summary.grid9_stop_ratio * 100 },
    { name: '平均速度', grid4: data.vr_summary.grid4_speed_mean, grid9: data.vr_summary.grid9_speed_mean },
  ];

  // 量表柱状图
  const scaleData = [
    { name: 'MMSE', value: data.scale_scores.MMSE, max: 30 },
    { name: 'MoCA', value: data.scale_scores.MOCA, max: 30 },
    { name: 'CDR-G', value: data.scale_scores.CDR_global, max: 3 },
    { name: 'CDR-SB', value: data.scale_scores.CDR_SB, max: 18 },
    { name: 'HIS', value: data.scale_scores.HIS, max: 18 },
  ];

  return (
    <div>
      <div className="page-header">
        <button
          onClick={() => navigate('/subjects')}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-primary)',
            cursor: 'pointer',
            fontSize: 14,
            marginBottom: 8,
          }}
        >
          ← 返回列表
        </button>
        <h1>🧍 {data.subject_id} 个体评估</h1>
        <p>
          风险等级：
          <span className={riskClass(data.risk.level)}>{data.risk.level}</span>
          &nbsp;&nbsp; 概率：{(data.risk.probability * 100).toFixed(0)}%
        </p>
      </div>

      {/* 量表分数 */}
      <div className="card">
        <div className="card-title">📋 传统量表分数</div>
        <div style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
            <BarChart data={scaleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 四宫格 vs 九宫格 雷达图 */}
      <div className="card">
        <div className="card-title">🎯 四宫格 vs 九宫格 行为对比</div>
        <div style={{ height: 350 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="name" fontSize={12} />
              <PolarRadiusAxis fontSize={10} />
              <Radar name="四宫格" dataKey="grid4" stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.2} />
              <Radar name="九宫格" dataKey="grid9" stroke="var(--color-warning)" fill="var(--color-warning)" fillOpacity={0.2} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 解释 */}
      <div className="card">
        <div className="card-title">💡 关键异常指标</div>
        <ul className="explain-list">
          {data.explanations.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
