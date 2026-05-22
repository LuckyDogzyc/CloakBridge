import type { RefObject } from "react";

type FileDropProps = {
  inputRef?: RefObject<HTMLTextAreaElement>;
  onFilesSelected: (files: File[]) => void;
  onChange: (value: string) => void;
  onUseSelection: () => void;
  value: string;
};

export function FileDrop({ inputRef, value, onChange, onFilesSelected, onUseSelection }: FileDropProps) {
  async function handleFiles(files: FileList | null) {
    const firstFile = files?.[0];
    if (!firstFile) return;
    onFilesSelected(Array.from(files));
    if (firstFile.name.toLowerCase().endsWith(".txt")) {
      const text = typeof firstFile.text === "function" ? await firstFile.text() : await new Response(firstFile).text();
      onChange(text);
    }
  }

  return (
    <section className="panel input-panel">
      <div className="panel-heading">
        <div>
          <h2>本地内容</h2>
          <p>原文只在本机审阅，外部模型只接收脱敏后的内容。</p>
        </div>
        <label className="upload-control">
          <span>上传附件</span>
          <input
            accept=".txt,.docx,.xlsx"
            aria-label="上传附件"
            multiple
            onChange={(event) => void handleFiles(event.target.files)}
            type="file"
          />
        </label>
      </div>
      <textarea
        aria-label="本地内容"
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="粘贴需要脱敏的文字，或上传 txt/docx/xlsx 文件。"
      />
      <div className="selection-tools">
        <button onClick={onUseSelection} type="button">
          将选中内容加入脱敏
        </button>
        <span>选中遗漏内容后加入审阅队列，会生成对应替换词。</span>
      </div>
    </section>
  );
}
