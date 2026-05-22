import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "../src/App";

test("renders CloakBridge review workspace", () => {
  render(<App />);
  expect(screen.getByText("CloakBridge")).toBeInTheDocument();
  expect(screen.getByText("敏感项审阅")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "高亮审阅" })).toBeInTheDocument();
});

test("opens dictionary and model views from sidebar", () => {
  render(<App />);

  fireEvent.click(screen.getByRole("button", { name: "词库" }));
  expect(screen.getByRole("heading", { name: "词库管理" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "模型" }));
  expect(screen.getByRole("heading", { name: "模型网关" })).toBeInTheDocument();
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
            sanitized_text: "xxx项目服务器aa.bb.cc.dd 测试123456",
            token_map: {
              "xxx项目": "西调工程项目",
              "aa.bb.cc.dd": "10.18.2.4",
            },
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

  await waitFor(() => expect(screen.getByText("xxx项目服务器aa.bb.cc.dd 测试123456")).toBeInTheDocument());
  expect(screen.getByText("xxx项目")).toBeInTheDocument();
  expect(screen.getByText("aa.bb.cc.dd")).toBeInTheDocument();
});
