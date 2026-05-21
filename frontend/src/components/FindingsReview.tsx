import type { Finding } from "../api/client";

export function FindingsReview({ findings }: { findings: Finding[] }) {
  return (
    <section className="panel">
      <h2>敏感项审阅</h2>
      <div className="finding-list">
        {findings.map((finding, index) => (
          <label className="finding-row" key={`${finding.start}-${finding.end}-${index}`}>
            <input type="checkbox" defaultChecked />
            <span>{finding.text}</span>
            <code>{finding.entity_type}</code>
            <small>{finding.source}</small>
          </label>
        ))}
      </div>
    </section>
  );
}
