import { useEffect, useState } from "react";
import {
  createModelConfig,
  listModelConfigs,
  testModelConfig,
  type ModelConfig,
} from "../api/client";

const PROVIDERS = [
  { label: "Custom OpenAI-compatible", value: "custom-openai" },
  { label: "GLM / 智谱", value: "glm" },
  { label: "MiniMax", value: "minimax" },
  { label: "DeepSeek", value: "deepseek" },
  { label: "Qwen / 通义", value: "qwen" },
  { label: "OpenRouter", value: "openrouter" },
];

export function ProviderPanel() {
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("custom-openai");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    void listModelConfigs()
      .then((result) => setConfigs(result.model_configs))
      .catch(() => setStatus("模型配置暂时无法读取"));
  }, []);

  async function saveConfig() {
    if (!name.trim() || !model.trim() || !baseUrl.trim()) {
      setStatus("请填写配置名称、模型 ID 和 Base URL");
      return;
    }
    const created = await createModelConfig({
      api_key: apiKey,
      base_url: baseUrl,
      model,
      name,
      provider,
    });
    setConfigs((current) => [...current, created]);
    setStatus("配置已保存");
    setApiKey("");
  }

  async function runConnectionTest(config: ModelConfig) {
    const result = await testModelConfig(config.id);
    setStatus(result.message);
  }

  return (
    <div className="model-grid">
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>新建模型配置</h2>
            <p>API Key 加密保存在本机，外部模型只接收脱敏文本。</p>
          </div>
        </div>
        <div className="field-stack">
          <label>
            <span>配置名称</span>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="例如：智谱主模型" />
          </label>
          <label>
            <span>模型供应商</span>
            <select aria-label="模型供应商" value={provider} onChange={(event) => setProvider(event.target.value)}>
              {PROVIDERS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>模型 ID</span>
            <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="例如：glm-4-flash" />
          </label>
          <label>
            <span>Base URL</span>
            <input
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="https://open.bigmodel.cn/api/paas/v4"
            />
          </label>
          <label>
            <span>API Key</span>
            <input
              autoComplete="off"
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
            />
          </label>
        </div>
        <div className="form-actions">
          <button className="primary-action" onClick={() => void saveConfig()} type="button">
            保存配置
          </button>
        </div>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>已保存配置</h2>
            <p>这些连接只保存在当前机器。</p>
          </div>
        </div>
        <div className="model-list">
          {configs.map((config) => (
            <div className="model-row" key={config.id}>
              <div>
                <strong>{config.name}</strong>
                <span>{`${config.provider} / ${config.model}`}</span>
                <span>{config.masked_api_key}</span>
              </div>
              <button className="ghost-action" onClick={() => void runConnectionTest(config)} type="button">
                测试连接
              </button>
            </div>
          ))}
          {configs.length === 0 ? <div className="empty-state">还没有模型配置。</div> : null}
        </div>
        {status ? <div className="status-line">{status}</div> : null}
      </section>
    </div>
  );
}
