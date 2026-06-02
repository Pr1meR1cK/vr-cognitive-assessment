import { NavLink, Outlet } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', label: '数据概览', icon: '📊' },
  { to: '/subjects', label: '被试列表', icon: '👥' },
  { to: '/correlation', label: '相关性分析', icon: '🔗' },
  { to: '/model', label: '模型评估', icon: '🧠' },
  { to: '/import', label: '数据导入', icon: '📥' },
];

export default function Layout() {
  return (
    <div className="app-layout">
      {/* 侧边栏 */}
      <aside className="sidebar">
        <div className="sidebar-logo">🧬 VR 认知评估</div>
        <ul className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                {item.icon} {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </aside>

      {/* 内容区 */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
