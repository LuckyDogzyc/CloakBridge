export function FileDrop({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <section className="panel">
      <h2>本地内容</h2>
      <textarea
        aria-label="本地内容"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="粘贴需要脱敏的文字，文件上传会在后续任务接入。"
      />
    </section>
  );
}
