export type Finding = {
  text: string;
  entity_type: string;
  start: number;
  end: number;
  source: string;
  confidence: number;
};

export type AliasGroup = {
  id: number;
  entity_type: string;
  canonical: string;
  aliases: string[];
  scope: string;
};

export type AliasGroupInput = {
  aliases: string[];
  canonical: string;
  entity_type: string;
  scope?: string;
};

export type FileJobResult = {
  job_id: string;
  files: {
    filename: string;
    output_path: string;
    finding_count: number;
    preview_text: string;
    sanitized_preview: string;
    findings: Finding[];
  }[];
  token_map: Record<string, string>;
  token_prompt?: string;
};

export type ValidationResult = {
  unknown_tokens: string[];
  malformed_tokens: string[];
  generic_tokens: string[];
  restored_text: string;
};

export type ChatSendResult = {
  sanitized_text: string;
  restored_text: string;
  attachments: string[];
  validation: ValidationResult;
};

export type ModelConfig = {
  id: number;
  name: string;
  provider: string;
  model: string;
  base_url: string;
  masked_api_key: string;
  enabled: boolean;
};

export type ModelConfigInput = {
  name: string;
  provider: string;
  model: string;
  base_url: string;
  api_key: string;
};

export type ModelOptions = {
  base_url: string;
  default_model: string;
  models: string[];
};

export async function analyzeText(text: string) {
  const response = await fetch("/api/analyze-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, dictionary: [] }),
  });
  if (!response.ok) throw new Error("分析失败");
  return (await response.json()) as { findings: Finding[] };
}

export async function sanitizeText(text: string, findings: Finding[], alias_groups: AliasGroupInput[] = []) {
  const response = await fetch("/api/sanitize-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, findings, alias_groups }),
  });
  if (!response.ok) throw new Error("脱敏失败");
  return (await response.json()) as {
    sanitized_text: string;
    token_map: Record<string, string>;
    token_prompt?: string;
  };
}

export async function listAliasGroups() {
  const response = await fetch("/api/alias-groups");
  if (!response.ok) throw new Error("读取词库失败");
  return (await response.json()) as { alias_groups: AliasGroup[] };
}

export async function createAliasGroup(input: AliasGroupInput) {
  const response = await fetch("/api/alias-groups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...input, scope: input.scope ?? "project" }),
  });
  if (!response.ok) throw new Error("保存别名组失败");
  return (await response.json()) as AliasGroup;
}

export async function sanitizeFiles(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  formData.append("alias_groups", "[]");
  const response = await fetch("/api/jobs/sanitize-files", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error("文件脱敏失败");
  return (await response.json()) as FileJobResult;
}

export async function validateResponse(sanitized_text: string, token_map: Record<string, string>) {
  const response = await fetch("/api/validate-response", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sanitized_text, token_map }),
  });
  if (!response.ok) throw new Error("校验失败");
  return (await response.json()) as ValidationResult;
}

export async function sendChat(prompt: string, token_map: Record<string, string>, model_config_id?: number) {
  const response = await fetch("/api/chat/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, token_map, model_config_id }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "发送失败");
  }
  return (await response.json()) as ChatSendResult;
}

export async function listModelConfigs() {
  const response = await fetch("/api/model-configs");
  if (!response.ok) throw new Error("读取模型配置失败");
  return (await response.json()) as { model_configs: ModelConfig[] };
}

export async function createModelConfig(input: ModelConfigInput) {
  const response = await fetch("/api/model-configs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error("保存模型配置失败");
  return (await response.json()) as ModelConfig;
}

export async function loadModelOptions(provider: string, api_key: string, base_url = "") {
  const response = await fetch("/api/model-options", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, api_key, base_url }),
  });
  if (!response.ok) throw new Error("读取模型列表失败");
  return (await response.json()) as ModelOptions;
}

export async function testModelConfig(id: number) {
  const response = await fetch(`/api/model-configs/${id}/test`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("测试连接失败");
  return (await response.json()) as { ok: boolean; message: string };
}
