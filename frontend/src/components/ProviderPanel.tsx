export function ProviderPanel() {
  return (
    <section className="panel">
      <h2>模型</h2>
      <select aria-label="模型供应商" defaultValue="custom-openai">
        <option value="custom-openai">Custom OpenAI-compatible</option>
        <option value="glm">GLM / 智谱</option>
        <option value="minimax">MiniMax</option>
        <option value="deepseek">DeepSeek</option>
        <option value="qwen">Qwen / 通义</option>
        <option value="openrouter">OpenRouter</option>
      </select>
    </section>
  );
}
