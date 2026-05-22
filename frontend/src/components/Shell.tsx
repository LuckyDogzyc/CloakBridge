import type { ReactNode } from "react";

export type AppView = "review" | "dictionary" | "models";

type ShellProps = {
  activeView: AppView;
  children: ReactNode;
  onNavigate: (view: AppView) => void;
};

const NAV_ITEMS: { label: string; view: AppView }[] = [
  { label: "审阅", view: "review" },
  { label: "词库", view: "dictionary" },
  { label: "模型", view: "models" },
];

export function Shell({ activeView, children, onNavigate }: ShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">CB</span>
          <span>CloakBridge</span>
        </div>
        <nav className="nav-list" aria-label="主导航">
          {NAV_ITEMS.map((item) => (
            <button
              className={item.view === activeView ? "nav-item active" : "nav-item"}
              key={item.view}
              onClick={() => onNavigate(item.view)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <strong>本地边界</strong>
          <span>原文、词库和映射表只在本机处理。</span>
        </div>
      </aside>
      <main className="workspace">{children}</main>
    </div>
  );
}
