// 被试列表页
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchSubjects } from '../api';
import type { SubjectListItem } from '../api/types';

function riskClass(level: string) {
  if (level.includes('高')) return 'risk-tag risk-high';
  if (level.includes('中')) return 'risk-tag risk-mid';
  return 'risk-tag risk-low';
}

export default function Subjects() {
  const [subjects, setSubjects] = useState<SubjectListItem[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSubjects().then(setSubjects);
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>👥 被试列表</h1>
        <p>共 {subjects.length} 名被试，点击行查看个体详情</p>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>被试编号</th>
                <th>MMSE</th>
                <th>MoCA</th>
                <th>CDR-G</th>
                <th>CDR-SB</th>
                <th>HIS</th>
                <th>风险概率</th>
                <th>风险等级</th>
              </tr>
            </thead>
            <tbody>
              {subjects.map((s) => (
                <tr
                  key={s.subject_id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/subjects/${s.subject_id}`)}
                >
                  <td>
                    <strong>{s.subject_id}</strong>
                  </td>
                  <td>{s.MMSE}</td>
                  <td>{s.MOCA}</td>
                  <td>{s.CDR_global}</td>
                  <td>{s.CDR_SB}</td>
                  <td>{s.HIS}</td>
                  <td>{(s.risk_probability * 100).toFixed(0)}%</td>
                  <td>
                    <span className={riskClass(s.risk_level)}>
                      {s.risk_level}
                    </span>
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
