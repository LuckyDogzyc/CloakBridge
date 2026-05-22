import type { ValidationResult } from "../api/client";

export function ResponseViewer({
  onValidate,
  restored,
  sanitized,
  validation,
}: {
  onValidate: () => void;
  restored: string;
  sanitized: string;
  validation?: ValidationResult | null;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>外发与回复</h2>
          <p>文件任务先生成脱敏外发预览；AI 返回后再做校验和本地恢复。</p>
        </div>
        <button className="ghost-action" disabled={!sanitized} onClick={onValidate} type="button">
          校验
        </button>
      </div>
      <div className="restored-response">{restored || "恢复后的回复会显示在这里。"}</div>
      {validation ? (
        <div className="validation-list">
          <span>泛指 {validation.generic_tokens.length}</span>
          <span>未知 {validation.unknown_tokens.length}</span>
          <span>坏标记 {validation.malformed_tokens.length}</span>
        </div>
      ) : null}
      <details>
        <summary>查看脱敏版本</summary>
        <pre>{sanitized}</pre>
      </details>
    </section>
  );
}
