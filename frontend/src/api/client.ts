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

export type FileJobResult = {
  job_id: string;
  files: {
    filename: string;
    output_path: string;
    finding_count: number;
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

export async function analyzeText(text: string) {
  const response = await fetch("/api/analyze-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, dictionary: [] }),
  });
  if (!response.ok) throw new Error("分析失败");
  return (await response.json()) as { findings: Finding[] };
}

export async function sanitizeText(text: string, findings: Finding[]) {
  const response = await fetch("/api/sanitize-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, findings }),
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

export async function createAliasGroup(input: {
  aliases: string[];
  canonical: string;
  entity_type: string;
  scope?: string;
}) {
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
