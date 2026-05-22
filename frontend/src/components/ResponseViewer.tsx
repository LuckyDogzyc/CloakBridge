import { useEffect, useMemo, useState } from "react";
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
  const [task, setTask] = useState("将文件模板提取出来，把正文内容改成编写指导，供另一个版本复用。");
  const [sanitizedDraft, setSanitizedDraft] = useState(sanitized);
  const [outboundPrompt, setOutboundPrompt] = useState("");

  useEffect(() => {
    setSanitizedDraft(sanitized);
  }, [sanitized]);

  const canCompose = sanitizedDraft.trim().length > 0 && task.trim().length > 0;

  const outboundPreview = useMemo(() => {
    if (!outboundPrompt) return "外发请求会在脱敏后生成。";
    return outboundPrompt;
  }, [outboundPrompt]);

  function composeOutboundPrompt() {
    if (!canCompose) return;
    setOutboundPrompt(
      [
        "你会处理一份已经脱敏的本地文件内容。",
        "请保持 [[...]] 形式的脱敏标记完全不变，不要改写、翻译或删除这些标记。",
        "",
        `任务：${task.trim()}`,
        "",
        "脱敏内容：",
        sanitizedDraft.trim(),
      ].join("\n"),
    );
  }

  return (
    <section className="panel ai-workbench">
      <div className="panel-heading">
        <div>
          <h2>AI 任务工作台</h2>
          <p>在这里写给外部大模型的任务，只把脱敏内容放进外发请求。</p>
        </div>
      </div>
      <div className="field-stack">
        <label>
          <span>给外部大模型的任务</span>
          <textarea
            className="compact-textarea"
            value={task}
            onChange={(event) => setTask(event.target.value)}
            placeholder="例如：提取模板，并把正文改成写作指导"
          />
        </label>
        <label>
          <span>脱敏外发内容</span>
          <textarea
            className="compact-textarea"
            value={sanitizedDraft}
            onChange={(event) => setSanitizedDraft(event.target.value)}
            placeholder="处理文件或点击脱敏后，这里会出现可发给外部模型的脱敏内容。"
          />
        </label>
      </div>
      <div className="form-actions split-actions">
        <button disabled={!canCompose} onClick={composeOutboundPrompt} type="button">
          生成外发请求
        </button>
        <button className="ghost-action" disabled={!sanitizedDraft} onClick={onValidate} type="button">
          校验回复
        </button>
      </div>
      <div className="outbound-preview" aria-label="脱敏外发请求预览">
        {outboundPreview}
      </div>
      <h3>本地恢复结果</h3>
      <div className="restored-response">{restored || "AI 返回后，解除脱敏的结果会显示在这里。"}</div>
      {validation ? (
        <div className="validation-list">
          <span>泛指 {validation.generic_tokens.length}</span>
          <span>未知 {validation.unknown_tokens.length}</span>
          <span>坏标记 {validation.malformed_tokens.length}</span>
        </div>
      ) : null}
      <details>
        <summary>查看脱敏回复</summary>
        <pre>{sanitized}</pre>
      </details>
    </section>
  );
}
