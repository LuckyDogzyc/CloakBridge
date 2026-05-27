import { useEffect, useState } from "react";
import {
  createModelConfig,
  listModelConfigs,
  loadModelOptions,
  testModelConfig,
  type ModelConfig,
} from "../api/client";

const PROVIDERS = [
  { label: "GLM / 智谱", value: "glm" },
  { label: "MiniMax", value: "minimax" },
  { label: "Custom OpenAI-compatible", value: "custom-openai" },
  { label: "DeepSeek", value: "deepseek" },
  { label: "Qwen / 通义", value: "qwen" },
  { label: "OpenRouter", value: "openrouter" },
];

const PROVIDER_PRESETS: Record<string, { baseUrl: string; defaultModel: string; name: string }> = {
  glm: {
    baseUrl: "https://api.z.ai/api/paas/v4",
    defaultModel: "glm-5.1",
    name: "GLM 主模型",
  },
  minimax: {
    baseUrl: "https://api.minimax.chat/v1",
    defaultModel: "MiniMax-M1",
    name: "MiniMax 主模型",
  },
};

export function ProviderPanel() {
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("glm");
  const [model, setModel] = useState("glm-5.1");
  const [baseUrl, setBaseUrl] = useState("https://api.z.ai/api/paas/v4");
  const [apiKey, setApiKey] = useState("");
  const [modelOptions, setModelOptions] = useState<string[]>(["glm-5.1"]);
  const [status, setStatus] = useState("");
  const isPresetProvider = provider in PROVIDER_PRESETS;

  useEffect(() => {
    void listModelConfigs()
      .then((result) => setConfigs(result.model_configs))
      .catch(() => setStatus("模型配置暂时无法读取"));
  }, []);

  function updateProvider(nextProvider: string) {
    setProvider(nextProvider);
    const preset = PROVIDER_PRESETS[nextProvider];
    if (preset) {
      setBaseUrl(preset.baseUrl);
      setModel(preset.defaultModel);
      setModelOptions([preset.defaultModel]);
      if (!name.trim()) setName(preset.name);
      return;
    }
    setBaseUrl("");
    setModel("");
    setModelOptions([]);
  }

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

  async function refreshModelOptions() {
    if (isPresetProvider && !apiKey.trim()) {
      setStatus("请先填写 API Key");
      return;
    }
    const result = await loadModelOptions(provider, apiKey, baseUrl);
    setBaseUrl(result.base_url);
    setModelOptions(result.models);
    setModel((current) => (result.models.includes(current) ? current : result.default_model || result.models[0] || ""));
    setStatus("模型列表已更新");
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
            <select aria-label="模型供应商" value={provider} onChange={(event) => updateProvider(event.target.value)}>
              {PROVIDERS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          {isPresetProvider ? (
            <label>
              <span>模型</span>
              <select aria-label="模型" value={model} onChange={(event) => setModel(event.target.value)}>
                {modelOptions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <>
              <label>
                <span>模型 ID</span>
                <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="例如：gpt-4o-mini" />
              </label>
              <label>
                <span>Base URL</span>
                <input
                  value={baseUrl}
                  onChange={(event) => setBaseUrl(event.target.value)}
                  placeholder="https://api.example.com/v1"
                />
              </label>
            </>
          )}
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
        <div className="form-actions split-actions">
          {isPresetProvider ? (
            <button className="ghost-action" onClick={() => void refreshModelOptions()} type="button">
              读取模型列表
            </button>
          ) : null}
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
