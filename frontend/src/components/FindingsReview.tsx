import type { Finding } from "../api/client";

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
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>敏感项审阅</h2>
          <p>确认、排除或补充需要脱敏的内容。</p>
        </div>
        <button className="ghost-action" onClick={onMergeSelected} type="button">
          合并为同一实体
        </button>
      </div>
      {mergeStatus ? <div className="status-note">{mergeStatus}</div> : null}
      <div className="finding-list">
        {findings.map((finding, index) => (
          <label className="finding-row" key={findingKey(finding, index)}>
            <input
              checked={activeKeys[findingKey(finding, index)] !== false}
              onChange={(event) => onToggle(findingKey(finding, index), event.target.checked)}
              type="checkbox"
            />
            <span className="finding-text">{finding.text}</span>
            <code>{finding.entity_type}</code>
            <small>{finding.source}</small>
            <span className="replacement-token">{replacementByOriginal[finding.text] ?? "待生成"}</span>
          </label>
        ))}
        {findings.length === 0 ? <div className="empty-state">运行分析后，候选敏感项会出现在这里。</div> : null}
      </div>
    </section>
  );
}
