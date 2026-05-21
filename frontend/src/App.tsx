import { useState } from "react";
import { analyzeText, sanitizeText, type Finding } from "./api/client";
import { FileDrop } from "./components/FileDrop";
import { FindingsReview } from "./components/FindingsReview";
import { ProviderPanel } from "./components/ProviderPanel";
import { ResponseViewer } from "./components/ResponseViewer";
import { Shell } from "./components/Shell";

export function App() {
  const [text, setText] = useState("华东三期项目服务器10.18.2.4");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [sanitized, setSanitized] = useState("");
  const [restored, setRestored] = useState("");

  async function runAnalysis() {
    const analysis = await analyzeText(text);
    setFindings(analysis.findings);
  }

  async function runSanitize() {
    const result = await sanitizeText(text, findings);
    setSanitized(result.sanitized_text);
    setRestored(text);
  }

  return (
    <Shell>
      <div className="toolbar">
        <button onClick={runAnalysis}>分析</button>
        <button onClick={runSanitize}>脱敏</button>
      </div>
      <div className="grid">
        <FileDrop value={text} onChange={setText} />
        <FindingsReview findings={findings} />
        <ProviderPanel />
        <ResponseViewer restored={restored} sanitized={sanitized} />
      </div>
    </Shell>
  );
}
