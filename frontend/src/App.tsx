import { useMemo, useRef, useState } from "react";
import { analyzeText, sanitizeText, type Finding } from "./api/client";
import { FileDrop } from "./components/FileDrop";
import { FindingsReview } from "./components/FindingsReview";
import { ProviderPanel } from "./components/ProviderPanel";
import { ResponseViewer } from "./components/ResponseViewer";
import { ReviewHighlighter } from "./components/ReviewHighlighter";
import { Shell, type AppView } from "./components/Shell";

function findingKey(finding: Finding, index: number) {
  return `${finding.start}:${finding.end}:${finding.entity_type}:${finding.text}:${index}`;
}

export function App() {
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [activeView, setActiveView] = useState<AppView>("review");
  const [text, setText] = useState("华东三期项目服务器10.18.2.4");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [activeKeys, setActiveKeys] = useState<Record<string, boolean>>({});
  const [sanitized, setSanitized] = useState("");
  const [restored, setRestored] = useState("");
  const [tokenMap, setTokenMap] = useState<Record<string, string>>({});

  const replacementByOriginal = useMemo(() => {
    return Object.fromEntries(Object.entries(tokenMap).map(([token, original]) => [original, token]));
  }, [tokenMap]);

  async function runAnalysis() {
    const analysis = await analyzeText(text);
    setFindings(analysis.findings);
    setActiveKeys(
      Object.fromEntries(analysis.findings.map((finding, index) => [findingKey(finding, index), true])),
    );
  }

  async function runSanitize() {
    const selectedFindings = findings.filter((finding, index) => activeKeys[findingKey(finding, index)] !== false);
    const result = await sanitizeText(text, selectedFindings);
    setSanitized(result.sanitized_text);
    setRestored(text);
    setTokenMap(result.token_map);
  }

  function toggleFinding(key: string, enabled: boolean) {
    setActiveKeys((current) => ({ ...current, [key]: enabled }));
  }

  function addSelectionAsFinding() {
    const input = textAreaRef.current;
    if (!input || input.selectionStart === input.selectionEnd) return;

    const start = input.selectionStart;
    const end = input.selectionEnd;
    const selectedText = text.slice(start, end).trim();
    if (!selectedText) return;

    const finding: Finding = {
      confidence: 1,
      end,
      entity_type: "PROJECT",
      source: "manual",
      start,
      text: selectedText,
    };
    setFindings((current) => {
      const next = [...current, finding].sort((a, b) => a.start - b.start || a.end - b.end);
      setActiveKeys(Object.fromEntries(next.map((item, index) => [findingKey(item, index), true])));
      return next;
    });
  }

  return (
    <Shell activeView={activeView} onNavigate={setActiveView}>
      {activeView === "review" ? (
        <>
          <div className="workspace-header">
            <div>
              <h1>本地脱敏审阅</h1>
              <p>规则先扫一遍，本地中文模型再判断，确认后才把脱敏内容交给外部模型。</p>
            </div>
            <div className="toolbar">
              <button onClick={runAnalysis} type="button">
                分析
              </button>
              <button className="primary-action" onClick={runSanitize} type="button">
                脱敏
              </button>
            </div>
          </div>
          <div className="grid">
            <FileDrop
              inputRef={textAreaRef}
              onChange={setText}
              onUseSelection={addSelectionAsFinding}
              value={text}
            />
            <ReviewHighlighter
              activeKeys={activeKeys}
              findingKey={findingKey}
              findings={findings}
              text={text}
            />
            <FindingsReview
              activeKeys={activeKeys}
              findingKey={findingKey}
              findings={findings}
              onToggle={toggleFinding}
              replacementByOriginal={replacementByOriginal}
            />
            <ResponseViewer restored={restored} sanitized={sanitized} />
          </div>
        </>
      ) : null}
      {activeView === "dictionary" ? <DictionaryView /> : null}
      {activeView === "models" ? <ModelsView /> : null}
    </Shell>
  );
}

function DictionaryView() {
  return (
    <section className="view-page">
      <div className="workspace-header">
        <div>
          <h1>词库管理</h1>
          <p>确认后的敏感项会进入本地词库，下次优先由规则层处理。</p>
        </div>
      </div>
      <div className="panel table-panel">
        <div className="dictionary-stats">
          <span>项目名称</span>
          <strong>0</strong>
          <span>IP / 网段</span>
          <strong>0</strong>
          <span>组织与人员</span>
          <strong>0</strong>
        </div>
        <div className="empty-state">词库数据将保存在本机，不会提交到 GitHub。</div>
      </div>
    </section>
  );
}

function ModelsView() {
  return (
    <section className="view-page">
      <div className="workspace-header">
        <div>
          <h1>模型网关</h1>
          <p>配置 GLM、MiniMax 或 OpenAI-compatible 自定义模型，统一走脱敏后的请求。</p>
        </div>
      </div>
      <ProviderPanel />
      <div className="panel model-boundary">
        <h2>边界策略</h2>
        <p>敏感原文、词库、映射字典只在本地；外部请求前会再次做泄露检查。</p>
      </div>
    </section>
  );
}
