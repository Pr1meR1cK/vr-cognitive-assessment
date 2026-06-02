// 数据导入页（占位 — 等待 A 实现 POST /api/data/analyze）
export default function DataImport() {
  return (
    <div>
      <div className="page-header">
        <h1>📥 数据导入</h1>
        <p>上传 VR 日志和量表文件，触发数据处理与特征提取</p>
      </div>

      <div className="card" style={{ textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📂</div>
        <p style={{ color: 'var(--color-muted)', marginBottom: 16 }}>
          此功能等待 A 成员实现 POST /api/data/analyze 接口后接入
        </p>
        <div
          style={{
            border: '2px dashed var(--color-line)',
            borderRadius: 8,
            padding: 32,
            background: 'var(--color-bg)',
            color: 'var(--color-muted)',
            fontSize: 14,
          }}
        >
          拖拽文件到此处 或 点击选择
          <br />
          <small>支持 .log 和 .xlsx 文件</small>
        </div>
      </div>

      <div className="card">
        <div className="card-title">📋 接口约定</div>
        <table>
          <thead>
            <tr>
              <th>方法</th>
              <th>路径</th>
              <th>负责人</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>POST</td>
              <td>/api/data/analyze</td>
              <td>A</td>
              <td>上传并处理数据</td>
            </tr>
            <tr>
              <td>GET</td>
              <td>/api/data/summary</td>
              <td>A</td>
              <td>数据概览 ✅</td>
            </tr>
            <tr>
              <td>GET</td>
              <td>/api/data/log-manifest</td>
              <td>A</td>
              <td>日志归类清单</td>
            </tr>
            <tr>
              <td>GET</td>
              <td>/api/data/features</td>
              <td>A</td>
              <td>VR 特征表</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
