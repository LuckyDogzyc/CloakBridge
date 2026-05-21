export function ResponseViewer({ restored, sanitized }: { restored: string; sanitized: string }) {
  return (
    <section className="panel">
      <h2>回复</h2>
      <div className="restored-response">{restored || "恢复后的回复会显示在这里。"}</div>
      <details>
        <summary>查看脱敏回复</summary>
        <pre>{sanitized}</pre>
      </details>
    </section>
  );
}
