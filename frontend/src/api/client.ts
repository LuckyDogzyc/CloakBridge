export type Finding = {
  text: string;
  entity_type: string;
  start: number;
  end: number;
  source: string;
  confidence: number;
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
  return (await response.json()) as { sanitized_text: string; token_map: Record<string, string> };
}
