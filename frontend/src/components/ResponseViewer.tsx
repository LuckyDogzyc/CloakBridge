export function ResponseViewer({ restored, sanitized }: { restored: string; sanitized: string }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>回复</h2>
          <p>默认展示解除脱敏后的文本，脱敏版本折叠保留用于检查。</p>
        </div>
      </div>
      <div className="restored-response">{restored || "恢复后的回复会显示在这里。"}</div>
      <details>
        <summary>查看脱敏回复</summary>
        <pre>{sanitized}</pre>
      </details>
    </section>
  );
}
