import type { Finding } from "../api/client";

type ReviewHighlighterProps = {
  activeKeys: Record<string, boolean>;
  findings: Finding[];
  findingKey: (finding: Finding, index: number) => string;
  text: string;
};

export function ReviewHighlighter({ activeKeys, findings, findingKey, text }: ReviewHighlighterProps) {
  const segments = buildSegments(text, findings, activeKeys, findingKey);

  return (
    <section className="panel highlighter-panel">
      <div className="panel-heading">
        <div>
          <h2>高亮审阅</h2>
          <p>纯文本预览用于审阅 docx/xlsx/txt 提取内容，勾选项会进入脱敏映射。</p>
        </div>
      </div>
      <div className="highlight-surface" aria-label="高亮审阅结果">
        {segments.map((segment, index) =>
          segment.finding ? (
            <mark className={`entity entity-${segment.finding.entity_type.toLowerCase()}`} key={index}>
              {segment.text}
            </mark>
          ) : (
            <span key={index}>{segment.text}</span>
          ),
        )}
      </div>
    </section>
  );
}

function buildSegments(
  text: string,
  findings: Finding[],
  activeKeys: Record<string, boolean>,
  findingKey: (finding: Finding, index: number) => string,
) {
  const activeFindings = findings
    .map((finding, index) => ({ finding, key: findingKey(finding, index) }))
    .filter((entry) => activeKeys[entry.key] !== false)
    .sort((a, b) => a.finding.start - b.finding.start || b.finding.end - a.finding.end);

  const segments: { finding?: Finding; text: string }[] = [];
  let cursor = 0;

  for (const { finding } of activeFindings) {
    if (finding.start < cursor || finding.end <= finding.start) continue;
    if (finding.start > cursor) {
      segments.push({ text: text.slice(cursor, finding.start) });
    }
    segments.push({ finding, text: text.slice(finding.start, finding.end) });
    cursor = finding.end;
  }

  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor) });
  }

  return segments.length > 0 ? segments : [{ text }];
}
