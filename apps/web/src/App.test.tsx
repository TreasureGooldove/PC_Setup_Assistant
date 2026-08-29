import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import App from "./App";

// 轻量 DOM 测试依赖由浏览器环境提供；应用在 API 不可用时应自动进入演示模式。
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("智能装机搭子工作台", () => {
  it("renders request controls and three plan choices", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    expect(screen.getByText("智能装机搭子")).toBeTruthy();
    expect(screen.getByLabelText("预算")).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("tab", { name: /均衡耐用/ })).toBeTruthy());
    expect(screen.getByRole("tab", { name: /省心省预算/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /高性能释放/ })).toBeTruthy();
  });

  it("updates the profile from a natural-language message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    const input = screen.getByLabelText("输入你的装机需求");
    fireEvent.change(input, { target: { value: "预算 1 万，想要水冷和 N 卡" } });
    fireEvent.submit(input.closest("form")!);
    await waitFor(() => expect(screen.getByText(/预算约 10,000 元/)).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /生成我的方案/ }));
    await waitFor(() => expect(screen.getByText("三套方案已生成（本地演示）")).toBeTruthy(), { timeout: 2000 });
  });
});
