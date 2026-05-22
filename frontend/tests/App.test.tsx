import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { App } from "../src/App";

test("renders CloakBridge review workspace", () => {
  render(<App />);
  expect(screen.getByText("CloakBridge")).toBeInTheDocument();
  expect(screen.getByText("敏感项审阅")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "高亮审阅" })).toBeInTheDocument();
});

test("opens dictionary and model views from sidebar", async () => {
  render(<App />);

  fireEvent.click(screen.getByRole("button", { name: "词库" }));
  expect(screen.getByRole("heading", { name: "词库管理" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "模型" }));
  expect(screen.getByRole("heading", { name: "模型网关" })).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText("模型配置暂时无法读取")).toBeInTheDocument());
});

test("model view saves and tests a local provider config", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/model-configs" && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        expect(body.provider).toBe("glm");
        expect(body.model).toBe("glm-4-flash");
        expect(body.api_key).toBe("sk-local-secret");
        return new Response(
          JSON.stringify({
            id: 7,
            name: "智谱主模型",
            provider: "glm",
            model: "glm-4-flash",
            base_url: "https://open.bigmodel.cn/api/paas/v4",
            masked_api_key: "sk-****cret",
            enabled: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/model-configs/7/test") {
        return new Response(JSON.stringify({ ok: true, message: "配置可用" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ model_configs: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );

  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "模型" }));

  fireEvent.change(screen.getByLabelText("配置名称"), { target: { value: "智谱主模型" } });
  fireEvent.change(screen.getByLabelText("模型供应商"), { target: { value: "glm" } });
  fireEvent.change(screen.getByLabelText("模型 ID"), { target: { value: "glm-4-flash" } });
  fireEvent.change(screen.getByLabelText("Base URL"), {
    target: { value: "https://open.bigmodel.cn/api/paas/v4" },
  });
  fireEvent.change(screen.getByLabelText("API Key"), { target: { value: "sk-local-secret" } });
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

  await waitFor(() => expect(screen.getByText("智谱主模型")).toBeInTheDocument());
  expect(screen.getByText("sk-****cret")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "测试连接" }));
  await waitFor(() => expect(screen.getByText("配置可用")).toBeInTheDocument());
});

test("dictionary view creates a local alias group", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/alias-groups" && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        expect(body.canonical).toBe("西调工程");
        return new Response(
          JSON.stringify({
            id: 1,
            entity_type: "PROJECT",
            canonical: "西调工程",
            aliases: ["西调工程", "西调2025工程", "西调搬迁", "2025资源补强"],
            scope: "project",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify({ alias_groups: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );

  render(<App />);

  fireEvent.click(screen.getByRole("button", { name: "词库" }));
  fireEvent.change(screen.getByLabelText("规范名称"), { target: { value: "西调工程" } });
  fireEvent.change(screen.getByLabelText("别名"), {
    target: { value: "西调工程\n西调2025工程\n西调搬迁\n2025资源补强" },
  });
  fireEvent.click(screen.getByRole("button", { name: "保存别名组" }));

  await waitFor(() => expect(screen.getByText("西调2025工程")).toBeInTheDocument());
  expect(screen.getByText("西调搬迁")).toBeInTheDocument();
});

test("review view sends selected files to local file job", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (url === "/api/jobs/sanitize-files") {
        return new Response(
          JSON.stringify({
            job_id: "job-12345678",
            files: [
              {
                filename: "input.txt",
                output_path: "/local/output/input.txt",
                finding_count: 2,
                preview_text: "西调工程服务器10.18.2.18",
                sanitized_preview: "[[PRJ:001#001]]服务器[[IP:A.B.C.018]]",
                findings: [
                  { text: "西调工程", entity_type: "PROJECT", start: 0, end: 4, source: "dictionary", confidence: 1 },
                  { text: "10.18.2.18", entity_type: "IP_ADDRESS", start: 7, end: 17, source: "regex", confidence: 1 },
                ],
              },
            ],
            token_map: { "[[PRJ:001#001]]": "西调工程", "[[IP:A.B.C.018]]": "10.18.2.18" },
            token_prompt: "rules",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify({ findings: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );

  render(<App />);

  const file = new File(["西调工程"], "input.txt", { type: "text/plain" });
  fireEvent.change(screen.getByLabelText("上传附件"), { target: { files: [file] } });
  await waitFor(() => expect(screen.getByText("input.txt")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "处理文件" }));
  await waitFor(() => expect(screen.getByText(/job-1234/)).toBeInTheDocument());
  expect(screen.getByText(/\/local\/output\/input.txt/)).toBeInTheDocument();
  expect(screen.getAllByText("西调工程").length).toBeGreaterThan(0);
  expect(screen.getAllByText("10.18.2.18").length).toBeGreaterThan(0);
  expect(screen.getByLabelText("脱敏外发内容")).toHaveValue("[[PRJ:001#001]]服务器[[IP:A.B.C.018]]");
});

test("review view groups duplicate findings and toggles them together", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/analyze-text") {
        return new Response(
          JSON.stringify({
            findings: [
              { text: "12306.cn", entity_type: "DOMAIN", start: 0, end: 8, source: "regex", confidence: 1 },
              { text: "12306.cn", entity_type: "DOMAIN", start: 11, end: 19, source: "regex", confidence: 1 },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/sanitize-text") {
        const body = JSON.parse(String(init?.body));
        expect(body.findings).toEqual([]);
        return new Response(JSON.stringify({ sanitized_text: body.text, token_map: {} }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ alias_groups: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );

  render(<App />);
  fireEvent.change(screen.getByLabelText("本地内容"), { target: { value: "12306.cn 和 12306.cn" } });
  fireEvent.click(screen.getByRole("button", { name: "分析" }));

  await waitFor(() => expect(screen.getByText("出现 2 次")).toBeInTheDocument());
  const reviewPanel = screen.getByRole("region", { name: "敏感项审阅" });
  expect(within(reviewPanel).getAllByText("12306.cn")).toHaveLength(1);

  fireEvent.click(screen.getByLabelText("12306.cn DOMAIN 出现 2 次"));
  fireEvent.click(screen.getByRole("button", { name: "脱敏" }));
});

test("review view provides an AI task composer after sanitized content exists", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("给外部大模型的任务"), {
    target: { value: "提取模板，并把正文改成写作指导" },
  });

  expect(screen.getByText("外发请求会在脱敏后生成。")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("脱敏外发内容"), {
    target: { value: "[[PRJ:001#001]]服务器[[IP:A.B.C.004]]" },
  });
  fireEvent.click(screen.getByRole("button", { name: "生成外发请求" }));

  const outboundPreview = screen.getByLabelText("脱敏外发请求预览");
  expect(outboundPreview).toHaveTextContent("提取模板，并把正文改成写作指导");
  expect(outboundPreview).toHaveTextContent("[[PRJ:001#001]]服务器[[IP:A.B.C.004]]");
});

test("review view merges selected project findings into one alias group before sanitizing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/analyze-text") {
        return new Response(
          JSON.stringify({
            findings: [
              { text: "西调工程", entity_type: "PROJECT", start: 0, end: 4, source: "manual", confidence: 1 },
              { text: "西调搬迁", entity_type: "PROJECT", start: 12, end: 16, source: "manual", confidence: 1 },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/alias-groups" && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        expect(body.canonical).toBe("西调工程");
        expect(body.aliases).toEqual(["西调工程", "西调搬迁"]);
        return new Response(
          JSON.stringify({
            id: 2,
            entity_type: "PROJECT",
            canonical: "西调工程",
            aliases: ["西调工程", "西调搬迁"],
            scope: "project",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/sanitize-text") {
        const body = JSON.parse(String(init?.body));
        expect(body.alias_groups[0].aliases).toEqual(["西调工程", "西调搬迁"]);
        return new Response(
          JSON.stringify({
            sanitized_text: "[[PRJ:001#001]]和[[PRJ:001#002]]",
            token_map: {
              "[[PRJ:001]]": "西调工程",
              "[[PRJ:001#001]]": "西调工程",
              "[[PRJ:001#002]]": "西调搬迁",
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify({ alias_groups: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );

  render(<App />);

  fireEvent.change(screen.getByLabelText("本地内容"), { target: { value: "西调工程和西调搬迁" } });
  fireEvent.click(screen.getByRole("button", { name: "分析" }));
  await waitFor(() => expect(screen.getByText("西调搬迁")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "合并为同一实体" }));
  await waitFor(() => expect(screen.getByText("已合并 2 个别名")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "脱敏" }));
  await waitFor(() => expect(screen.getByText("[[PRJ:001#001]]和[[PRJ:001#002]]")).toBeInTheDocument());
});

test("review view exposes upload, highlighted text, and replacement map", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/analyze-text") {
        return new Response(
          JSON.stringify({
            findings: [
              {
                text: "西调工程项目",
                entity_type: "PROJECT",
                start: 0,
                end: 6,
                source: "local_ai:heuristic",
                confidence: 0.72,
              },
              {
                text: "10.18.2.4",
                entity_type: "IP_ADDRESS",
                start: 9,
                end: 18,
                source: "regex",
                confidence: 1,
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/sanitize-text") {
        const body = JSON.parse(String(init?.body));
        expect(body.text).toContain("西调工程项目");
        return new Response(
          JSON.stringify({
            sanitized_text: "[[PRJ:001#001]]服务器[[IP:A.B.C.004]] 测试123456",
            token_map: {
              "[[PRJ:001]]": "西调工程项目",
              "[[PRJ:001#001]]": "西调工程项目",
              "[[IP:A.B.C.004]]": "10.18.2.4",
            },
            token_prompt: "token rules",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url === "/api/validate-response") {
        return new Response(
          JSON.stringify({
            unknown_tokens: [],
            malformed_tokens: [],
            generic_tokens: ["[[PRJ:001]]"],
            restored_text: "西调工程项目服务器10.18.2.4 测试123456",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response("not found", { status: 404 });
    }),
  );

  render(<App />);

  expect(screen.getByText("上传附件")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("本地内容"), {
    target: { value: "西调工程项目服务器10.18.2.4 测试123456" },
  });
  fireEvent.click(screen.getByRole("button", { name: "分析" }));

  await waitFor(() => expect(screen.getAllByText("西调工程项目").length).toBeGreaterThan(0));
  expect(screen.getAllByText("10.18.2.4").length).toBeGreaterThan(0);
  expect(screen.getByText("local_ai:heuristic")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "脱敏" }));

  await waitFor(() =>
    expect(screen.getByText("[[PRJ:001#001]]服务器[[IP:A.B.C.004]] 测试123456")).toBeInTheDocument(),
  );
  expect(screen.getByText("[[PRJ:001#001]]")).toBeInTheDocument();
  expect(screen.getByText("[[IP:A.B.C.004]]")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "校验回复" }));
  await waitFor(() => expect(screen.getByText("泛指 1")).toBeInTheDocument());
});
