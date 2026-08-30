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
    expect(document.querySelector('[data-theme="corporate"]')).toBeTruthy();
    expect(screen.getByLabelText("预算")).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("tab", { name: /均衡耐用/ })).toBeTruthy());
    expect(screen.getByRole("tab", { name: /省心省预算/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /高性能释放/ })).toBeTruthy();
  });

  it("updates the profile from a natural-language message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    const input = screen.getByLabelText("输入你的装机需求");
    fireEvent.change(input, { target: { value: "预算 1 万，想要水冷、N 卡和 ITX 小钢炮" } });
    fireEvent.submit(input.closest("form")!);
    await waitFor(() => expect(screen.getByText(/预算约 10,000 元/)).toBeTruthy());
    expect(screen.getByRole("button", { name: "ITX 小钢炮" }).className).toContain("selected");
    fireEvent.click(screen.getByRole("button", { name: /生成我的方案/ }));
    await waitFor(() => expect(screen.getByText("三套方案已生成（本地演示）")).toBeTruthy(), { timeout: 2000 });
  });

  it("opens the ladder, game requirements, and theme settings views", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "硬件天梯" }));
    expect(screen.getAllByText("硬件天梯").length).toBeGreaterThan(0);
    expect(screen.getByText("GeForce RTX 4070 SUPER")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "游戏配置" }));
    expect(screen.getByText("游戏能不能带得动？")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Counter-Strike 2/ }));
    await waitFor(() => expect(screen.getByText("最低配置")).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "设置" }));
    fireEvent.click(screen.getByRole("button", { name: /企业简洁风/ }));
    expect(document.querySelector('[data-theme="corporate"]')).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /新拟物派/ }));
    expect(document.querySelector('[data-theme="neumorphism"]')).toBeTruthy();
  });

  it("finds War Thunder from the common warthuder typo", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "游戏配置" }));
    const input = screen.getByLabelText("搜索游戏");
    fireEvent.change(input, { target: { value: "warthuder" } });
    fireEvent.submit(input.closest("form")!);
    await waitFor(() => expect(screen.getByRole("button", { name: /War Thunder/ })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /War Thunder/ }));
    await waitFor(() => expect(screen.getByText("95 GB 可用空间")).toBeTruthy());
  });

  it("opens hardware details from the ladder and supports selecting a candidate", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "硬件天梯" }));
    const ladderName = await screen.findByText("GeForce RTX 4070 SUPER");
    fireEvent.click(ladderName.closest("button")!);
    expect(await screen.findByRole("dialog", { name: "选择显卡" })).toBeTruthy();
    expect(screen.getByText("配件详情")).toBeTruthy();
    expect(screen.getByRole("button", { name: "使用此显卡" })).toBeTruthy();
  });

  it("does not request an export for a demo plan after the API connects", async () => {
    const conversation = {
      id: "conversation-test",
      profile: { budget: 8000, use_case: "游戏与日常", resolution: "2K", refresh_rate: 165, cpu_brand: "any", gpu_brand: "any", cooling: "any", form_factor: "any", aesthetics: "简洁", noise: "均衡", upgrade: "保留升级空间", existing_parts: [] },
      messages: [{ role: "assistant", content: "你好", created_at: new Date().toISOString() }],
    };
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(conversation), { status: 200, headers: { "Content-Type": "application/json" } })).mockRejectedValue(new Error("unexpected request"));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await waitFor(() => expect(screen.getByText("API 已连接")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /导出清单/ }));
    expect(screen.getByText(/当前是演示预览/)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
