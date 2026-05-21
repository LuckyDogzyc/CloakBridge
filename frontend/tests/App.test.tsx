import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { App } from "../src/App";

test("renders CloakBridge review workspace", () => {
  render(<App />);
  expect(screen.getByText("CloakBridge")).toBeInTheDocument();
  expect(screen.getByText("敏感项审阅")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "模型" })).toBeInTheDocument();
});
