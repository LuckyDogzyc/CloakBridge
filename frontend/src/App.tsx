import { useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeText,
  createAliasGroup,
  listAliasGroups,
  sanitizeText,
  sanitizeFiles,
  validateResponse,
  type AliasGroup,
  type AliasGroupInput,
  type FileJobResult,
  type Finding,
  type ValidationResult,
} from "./api/client";
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
  const [text, setText] = useState("");
  const [promptText, setPromptText] = useState("");
  const [filePreviewText, setFilePreviewText] = useState("");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [activeKeys, setActiveKeys] = useState<Record<string, boolean>>({});
  const [sanitized, setSanitized] = useState("");
  const [tokenMap, setTokenMap] = useState<Record<string, string>>({});
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fileJob, setFileJob] = useState<FileJobResult | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [reviewAliasGroups, setReviewAliasGroups] = useState<AliasGroupInput[]>([]);
  const [mergeStatus, setMergeStatus] = useState("");
  const [lastAnalyzedText, setLastAnalyzedText] = useState("");

  const replacementByOriginal = useMemo(() => {
    return Object.fromEntries(Object.entries(tokenMap).map(([token, original]) => [original, token]));
  }, [tokenMap]);

  async function runAnalysis() {
    const analysis = await analyzeText(text);
    const nextFindings = Array.isArray(analysis.findings) ? analysis.findings : [];
    setFindings(nextFindings);
    activateFindings(nextFindings);
    setLastAnalyzedText(text);
    return nextFindings;
  }

  async function runSanitize() {
    if (!text.trim()) return;
    const currentFindings = lastAnalyzedText === text ? findings : await runAnalysis();
    const currentActiveKeys =
      lastAnalyzedText === text
        ? activeKeys
        : Object.fromEntries(currentFindings.map((finding, index) => [findingKey(finding, index), true]));
    const selectedFindings = currentFindings.filter(
      (finding, index) => currentActiveKeys[findingKey(finding, index)] !== false,
    );
    const result = await sanitizeText(text, selectedFindings, reviewAliasGroups);
    setSanitized(result.sanitized_text);
    setTokenMap(result.token_map);
    setValidation(null);
  }

  async function runFileSanitize(files: File[]) {
    if (files.length === 0) return;
    setSelectedFiles(files);
    const result = await sanitizeFiles(files);
    setFileJob(result);
    setTokenMap(result.token_map);
    const firstPreview = result.files[0];
    if (firstPreview) {
      setFilePreviewText(firstPreview.preview_text);
      setText([promptText, firstPreview.preview_text].filter(Boolean).join("\n\n"));
      setFindings(firstPreview.findings);
      activateFindings(firstPreview.findings);
      setLastAnalyzedText(firstPreview.preview_text);
      setSanitized(firstPreview.sanitized_preview);
      setValidation(null);
    }
  }

  function handleFilesSelected(files: File[]) {
    void runFileSanitize(files);
  }

  function handlePromptChange(value: string) {
    setPromptText(value);
    setText([value, filePreviewText].filter(Boolean).join("\n\n"));
    setSanitized("");
    setTokenMap({});
    setValidation(null);
    setLastAnalyzedText("");
    setFindings([]);
    setActiveKeys({});
  }

  async function runResponseValidation() {
    const result = await validateResponse(sanitized, tokenMap);
    setValidation(result);
  }

  function toggleFinding(key: string, enabled: boolean) {
    setActiveKeys((current) => ({ ...current, [key]: enabled }));
  }

  function activateFindings(nextFindings: Finding[]) {
    setActiveKeys(Object.fromEntries(nextFindings.map((finding, index) => [findingKey(finding, index), true])));
  }

  async function mergeSelectedFindings() {
    const selectedProjectTexts = findings
      .filter((finding, index) => activeKeys[findingKey(finding, index)] !== false)
      .filter((finding) => finding.entity_type === "PROJECT")
      .map((finding) => finding.text);
    const aliases = Array.from(new Set(selectedProjectTexts));
    if (aliases.length < 2) {
      setMergeStatus("至少选择 2 个项目候选项");
      return;
    }
    const group: AliasGroupInput = {
      aliases,
      canonical: aliases[0],
      entity_type: "PROJECT",
    };
    await createAliasGroup(group);
    setReviewAliasGroups((current) => [...current, group]);
    setMergeStatus(`已合并 ${aliases.length} 个别名`);
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
              <button className="primary-action" disabled={!text.trim()} onClick={runSanitize} type="button">
                脱敏
              </button>
            </div>
          </div>
          <div className="grid">
            <ResponseViewer
              files={selectedFiles}
              job={fileJob}
              onFilesSelected={handleFilesSelected}
              onPromptChange={handlePromptChange}
              onValidate={() => void runResponseValidation()}
              promptText={promptText}
              sanitized={sanitized}
              tokenMap={tokenMap}
              validation={validation}
            />
            <section className="review-column">
              <div className="review-text-editor">
                <div className="review-editor-header">
                  <span>脱敏审阅纯文本</span>
                  <button className="ghost-action" onClick={addSelectionAsFinding} type="button">
                    加入脱敏
                  </button>
                </div>
                <textarea
                  aria-label="脱敏审阅纯文本"
                  ref={textAreaRef}
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                />
              </div>
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
                mergeStatus={mergeStatus}
                onMergeSelected={() => void mergeSelectedFindings()}
                onToggle={toggleFinding}
                replacementByOriginal={replacementByOriginal}
              />
            </section>
          </div>
        </>
      ) : null}
      {activeView === "dictionary" ? <DictionaryView /> : null}
      {activeView === "models" ? <ModelsView /> : null}
    </Shell>
  );
}

function DictionaryView() {
  const [aliasGroups, setAliasGroups] = useState<AliasGroup[]>([]);
  const [canonical, setCanonical] = useState("");
  const [aliasesText, setAliasesText] = useState("");

  useEffect(() => {
    void listAliasGroups()
      .then((result) => setAliasGroups(result.alias_groups))
      .catch(() => setAliasGroups([]));
  }, []);

  async function saveAliasGroup() {
    const aliases = aliasesText
      .split(/\r?\n|,/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (!canonical.trim() || aliases.length === 0) return;

    const created = await createAliasGroup({
      aliases,
      canonical: canonical.trim(),
      entity_type: "PROJECT",
    });
    setAliasGroups((current) => [...current, created]);
    setCanonical("");
    setAliasesText("");
  }

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
      <div className="dictionary-layout">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>新建别名组</h2>
              <p>把多个叫法归为同一个实体，恢复时仍保留原始写法。</p>
            </div>
          </div>
          <div className="field-stack">
            <label>
              <span>规范名称</span>
              <input value={canonical} onChange={(event) => setCanonical(event.target.value)} />
            </label>
            <label>
              <span>别名</span>
              <textarea
                className="compact-textarea"
                value={aliasesText}
                onChange={(event) => setAliasesText(event.target.value)}
                placeholder="每行一个别名，例如：西调工程"
              />
            </label>
          </div>
          <div className="form-actions">
            <button className="primary-action" onClick={() => void saveAliasGroup()} type="button">
              保存别名组
            </button>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>本地别名组</h2>
              <p>这些数据只保存在当前机器。</p>
            </div>
          </div>
          <div className="alias-list">
            {aliasGroups.map((group) => (
              <div className="alias-row" key={group.id}>
                <strong>{group.canonical}</strong>
                <div className="alias-tags">
                  {group.aliases.map((alias) => (
                    <span key={alias}>{alias}</span>
                  ))}
                </div>
              </div>
            ))}
            {aliasGroups.length === 0 ? <div className="empty-state">还没有别名组。</div> : null}
          </div>
        </section>
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
