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
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fileJob, setFileJob] = useState<FileJobResult | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [reviewAliasGroups, setReviewAliasGroups] = useState<AliasGroupInput[]>([]);
  const [mergeStatus, setMergeStatus] = useState("");

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
    const result = await sanitizeText(text, selectedFindings, reviewAliasGroups);
    setSanitized(result.sanitized_text);
    setRestored(text);
    setTokenMap(result.token_map);
  }

  async function runFileSanitize() {
    if (selectedFiles.length === 0) return;
    const result = await sanitizeFiles(selectedFiles);
    setFileJob(result);
    setTokenMap(result.token_map);
  }

  async function runResponseValidation() {
    const result = await validateResponse(sanitized, tokenMap);
    setValidation(result);
    setRestored(result.restored_text);
  }

  function toggleFinding(key: string, enabled: boolean) {
    setActiveKeys((current) => ({ ...current, [key]: enabled }));
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
              onFilesSelected={setSelectedFiles}
              onUseSelection={addSelectionAsFinding}
              value={text}
            />
            <FileJobPanel files={selectedFiles} job={fileJob} onRun={runFileSanitize} />
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
            <ResponseViewer
              onValidate={() => void runResponseValidation()}
              restored={restored}
              sanitized={sanitized}
              validation={validation}
            />
          </div>
        </>
      ) : null}
      {activeView === "dictionary" ? <DictionaryView /> : null}
      {activeView === "models" ? <ModelsView /> : null}
    </Shell>
  );
}

function FileJobPanel({
  files,
  job,
  onRun,
}: {
  files: File[];
  job: FileJobResult | null;
  onRun: () => Promise<void>;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>文件任务</h2>
          <p>多个文件共用同一个映射字典。</p>
        </div>
        <button className="ghost-action" disabled={files.length === 0} onClick={() => void onRun()} type="button">
          处理文件
        </button>
      </div>
      <div className="file-list">
        {files.map((file) => (
          <span key={`${file.name}-${file.size}`}>{file.name}</span>
        ))}
        {files.length === 0 ? <div className="empty-state">选择 txt/docx/xlsx 后会出现在这里。</div> : null}
      </div>
      {job ? (
        <div className="job-result">
          <strong>任务 {job.job_id.slice(0, 8)}</strong>
          {job.files.map((file) => (
            <span key={file.output_path}>
              {`${file.filename} -> ${file.output_path}`}
            </span>
          ))}
        </div>
      ) : null}
    </section>
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
