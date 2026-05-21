import type { ReactNode } from "react";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">CloakBridge</div>
        <button className="nav-item active">审阅</button>
        <button className="nav-item">词库</button>
        <button className="nav-item">模型</button>
      </aside>
      <main className="workspace">{children}</main>
    </div>
  );
}
