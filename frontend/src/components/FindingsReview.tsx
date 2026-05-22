import type { Finding } from "../api/client";

type FindingGroup = {
  entity_type: string;
  findings: { finding: Finding; key: string }[];
  text: string;
};

type FindingsReviewProps = {
  activeKeys: Record<string, boolean>;
  findingKey: (finding: Finding, index: number) => string;
  findings: Finding[];
  mergeStatus?: string;
  onMergeSelected: () => void;
  onToggle: (key: string, enabled: boolean) => void;
  replacementByOriginal: Record<string, string>;
};

export function FindingsReview({
  activeKeys,
  findingKey,
  findings,
  mergeStatus,
  onMergeSelected,
  onToggle,
  replacementByOriginal,
}: FindingsReviewProps) {
  const groups = groupFindings(findings, findingKey);

  return (
    <section aria-label="敏感项审阅" className="panel">
      <div className="panel-heading">
        <div>
          <h2>敏感项审阅</h2>
          <p>相同敏感项合并显示，开关一次会影响所有出现位置。</p>
        </div>
        <button className="ghost-action" onClick={onMergeSelected} type="button">
          合并为同一实体
        </button>
      </div>
      {mergeStatus ? <div className="status-note">{mergeStatus}</div> : null}
      <div className="finding-list">
        {groups.map((group) => {
          const firstFinding = group.findings[0].finding;
          const allEnabled = group.findings.every((entry) => activeKeys[entry.key] !== false);
          const replacement = replacementByOriginal[group.text] ?? "待生成";
          return (
          <label className="finding-row" key={`${group.entity_type}:${group.text}`}>
            <input
              aria-label={`${group.text} ${group.entity_type} 出现 ${group.findings.length} 次`}
              checked={allEnabled}
              onChange={(event) => {
                for (const entry of group.findings) {
                  onToggle(entry.key, event.target.checked);
                }
              }}
              type="checkbox"
            />
            <span className="finding-text">{group.text}</span>
            <code>{group.entity_type}</code>
            <small>{firstFinding.source}</small>
            <span className="occurrence-count">出现 {group.findings.length} 次</span>
            <span className="replacement-token">{replacement}</span>
          </label>
          );
        })}
        {findings.length === 0 ? <div className="empty-state">运行分析后，候选敏感项会出现在这里。</div> : null}
      </div>
    </section>
  );
}

function groupFindings(
  findings: Finding[],
  findingKey: (finding: Finding, index: number) => string,
): FindingGroup[] {
  const groups = new Map<string, FindingGroup>();
  findings.forEach((finding, index) => {
    const key = `${finding.entity_type}:${finding.text}`;
    const current = groups.get(key);
    const entry = { finding, key: findingKey(finding, index) };
    if (current) {
      current.findings.push(entry);
      return;
    }
    groups.set(key, {
      entity_type: finding.entity_type,
      findings: [entry],
      text: finding.text,
    });
  });
  return Array.from(groups.values());
}
