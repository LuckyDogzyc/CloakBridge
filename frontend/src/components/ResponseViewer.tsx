import { useEffect, useState } from "react";
import {
  listModelConfigs,
  sendChat,
  type FileJobResult,
  type ModelConfig,
  type ValidationResult,
} from "../api/client";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  text: string;
  sanitized?: string;
};

export function ResponseViewer({
  files,
  job,
  onFilesSelected,
  onPromptChange,
  onValidate,
  promptText,
  sanitized,
  tokenMap,
  validation,
}: {
  files: File[];
  job: FileJobResult | null;
  onFilesSelected: (files: File[]) => void;
  onPromptChange: (value: string) => void;
  onValidate: () => void;
  promptText: string;
  sanitized: string;
  tokenMap: Record<string, string>;
  validation?: ValidationResult | null;
}) {
  const [modelConfigs, setModelConfigs] = useState<ModelConfig[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "assistant",
      text: "上传附件或输入 prompt 后，我会先在本地脱敏，再发送给外部模型。",
    },
  ]);

  useEffect(() => {
    void listModelConfigs()
      .then((result) => {
        const configs = Array.isArray(result.model_configs) ? result.model_configs : [];
        if (configs.length === 0) return;
        setModelConfigs(configs);
        setSelectedModelId((current) => current ?? configs[0]?.id);
      })
      .catch(() => {
        // Keep the composer usable without model metadata; the backend will report missing config on send.
      });
  }, []);

  function handleFiles(filesList: FileList | null) {
    const nextFiles = Array.from(filesList ?? []);
    if (nextFiles.length === 0) return;
    onFilesSelected(nextFiles);
  }

  function outboundPrompt() {
    if (!promptText.trim() || !sanitized.trim()) return "";
    return [
      "你会处理一份已经脱敏的本地文件内容。",
      "请保持 [[...]] 形式的脱敏标记完全不变，不要改写、翻译或删除这些标记。",
      "",
      `用户指令：${promptText.trim()}`,
      "",
      "脱敏内容：",
      sanitized.trim(),
    ].join("\n");
  }

  async function sendMessage() {
    const prompt = outboundPrompt();
    if (!prompt) return;
    setMessages((current) => [...current, { id: current.length + 1, role: "user", text: promptText.trim(), sanitized: prompt }]);
    try {
      const result = await sendChat(prompt, tokenMap, selectedModelId);
      setMessages((current) => [
        ...current,
        {
          id: current.length + 1,
          role: "assistant",
          text: result.restored_text,
          sanitized: result.sanitized_text,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: current.length + 1,
          role: "assistant",
          text: error instanceof Error ? error.message : "发送失败",
          sanitized: prompt,
        },
      ]);
    }
  }

  const prompt = outboundPrompt();

  return (
    <section className="chat-column">
      <div className="chat-header">
        <div>
          <h2>外部模型对话</h2>
          <p>中间列只展示脱敏后的交互内容；敏感项在右侧本地审阅。</p>
        </div>
      </div>
      <div className="chat-history" aria-label="外部模型交互记录">
        {messages.map((message) => (
          <article className={`chat-message ${message.role}`} key={message.id}>
            <div className="message-bubble">{message.text}</div>
            {message.role === "assistant" ? (
              <details>
                <summary>查看脱敏回复</summary>
                <pre>{message.sanitized ?? "暂无脱敏回复。"}</pre>
              </details>
            ) : null}
          </article>
        ))}
      </div>
      {validation ? (
        <div className="validation-list">
          <span>泛指 {validation.generic_tokens.length}</span>
          <span>未知 {validation.unknown_tokens.length}</span>
          <span>坏标记 {validation.malformed_tokens.length}</span>
        </div>
      ) : null}
      {job ? (
        <div className="job-result compact-job">
          {job.files.map((file) => (
            <span key={file.output_path}>{`${file.filename} -> ${file.output_path} / ${file.finding_count} 项`}</span>
          ))}
        </div>
      ) : null}
      <div className="composer">
        <div className="upload-chip-row">
          <label className="upload-control">
            <span>上传附件</span>
            <input
              accept=".txt,.docx,.xlsx"
              aria-label="上传附件"
              multiple
              onChange={(event) => handleFiles(event.target.files)}
              type="file"
            />
          </label>
          {files.map((file) => (
            <span className="file-chip" key={`${file.name}-${file.size}`}>
              {file.name}
            </span>
          ))}
          <label className="model-picker">
            <span>外部模型</span>
            <select
              aria-label="外部模型"
              disabled={modelConfigs.length === 0}
              value={selectedModelId ?? ""}
              onChange={(event) => setSelectedModelId(Number(event.target.value))}
            >
              {modelConfigs.length === 0 ? <option value="">未配置</option> : null}
              {modelConfigs.map((config) => (
                <option key={config.id} value={config.id}>
                  {`${config.name} / ${config.model}`}
                </option>
              ))}
            </select>
          </label>
        </div>
        <textarea
          aria-label="输入 prompt"
          className="prompt-input"
          value={promptText}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="输入要交给外部模型的任务。先脱敏，再发送。"
        />
        <div className="composer-actions">
          <button disabled={!prompt} onClick={sendMessage} type="button">
            发送
          </button>
          <button className="ghost-action" disabled={!sanitized} onClick={onValidate} type="button">
            校验回复
          </button>
        </div>
      </div>
    </section>
  );
}
