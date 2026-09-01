import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import App from "./App";

// 轻量 DOM 测试依赖由浏览器环境提供；应用在 API 不可用时应自动进入演示模式。
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("智能装机搭子工作台", () => {
  it("renders request controls and three plan choices", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    expect(screen.getByText("智能装机搭子")).toBeTruthy();
    expect(document.querySelector('[data-theme="corporate"]')).toBeTruthy();
    expect(screen.getByLabelText("预算")).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: /均衡耐用/ })).toBeTruthy(),
    );
    expect(screen.getByRole("tab", { name: /省心省预算/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /高性能释放/ })).toBeTruthy();
  });

  it("updates the profile from a natural-language message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    const input = screen.getByLabelText("输入你的装机需求");
    fireEvent.change(input, {
      target: { value: "预算 1 万，想要水冷、N 卡和 ITX 小钢炮" },
    });
    fireEvent.submit(input.closest("form")!);
    await waitFor(() =>
      expect(screen.getByText(/预算约 10,000 元/)).toBeTruthy(),
    );
    expect(
      screen.getByRole("button", { name: "ITX 小钢炮" }).className,
    ).toContain("selected");
    expect(screen.getByText("方案生成进度")).toBeTruthy();
    await waitFor(
      () => expect(screen.getByText("三套方案已生成（本地演示）")).toBeTruthy(),
      { timeout: 3000 },
    );
    expect(screen.getByText(/已更新到方案工作台/)).toBeTruthy();
  });

  it("accepts an exact custom budget and clamps invalid values", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    const customBudget = screen.getByRole("spinbutton", { name: "自定义预算" });

    fireEvent.change(customBudget, { target: { value: "12345" } });
    fireEvent.blur(customBudget);
    expect((customBudget as HTMLInputElement).value).toBe("12345");
    expect(screen.getByText("支持精确到 1 元，生成前会自动校准")).toBeTruthy();

    fireEvent.change(customBudget, { target: { value: "2000" } });
    expect(screen.getByText("最低预算为 ¥2,500")).toBeTruthy();
    fireEvent.blur(customBudget);
    expect((customBudget as HTMLInputElement).value).toBe("2500");

    fireEvent.change(customBudget, { target: { value: "12345" } });
    fireEvent.blur(customBudget);
    fireEvent.click(screen.getByRole("button", { name: /重新生成并核对/ }));
    expect(screen.getByText("方案生成进度")).toBeTruthy();
    await waitFor(
      () =>
        expect(
          screen.getByText("三套方案已生成（本地演示），已更新到方案工作台"),
        ).toBeTruthy(),
      { timeout: 2000 },
    );
  });

  it("uses a 2500 yuan budget and exposes the honest shortfall", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    const customBudget = screen.getByRole("spinbutton", { name: "自定义预算" });
    fireEvent.change(customBudget, { target: { value: "2500" } });
    fireEvent.blur(customBudget);
    fireEvent.click(screen.getByRole("button", { name: /重新生成并核对/ }));

    await waitFor(
      () => expect(screen.getByText(/预算不足以覆盖完整配置/)).toBeTruthy(),
      { timeout: 2000 },
    );
    expect(screen.getAllByText("¥2,500").length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText("¥12,292")).toBeNull();
  });

  it("recognizes War Thunder from a natural-language builder request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    const input = screen.getByLabelText("输入你的装机需求");
    fireEvent.change(input, {
      target: { value: "8000元玩战争雷霆的游戏主机" },
    });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() =>
      expect(document.querySelector(".recognized-game")?.textContent).toContain(
        "War Thunder",
      ),
    );
    expect(
      document.querySelector(".recognized-game small")?.textContent,
    ).toContain("最低/推荐配置已载入");
    expect(screen.getByText(/预算约 8,000 元/)).toBeTruthy();
  });

  it("passes the submitted profile to the API and falls back when generation is unavailable", async () => {
    const conversation = {
      id: "conversation-auto-generate",
      profile: {
        budget: 8000,
        use_case: "游戏与日常",
        resolution: "2K",
        refresh_rate: 165,
        cpu_brand: "any",
        gpu_brand: "any",
        cooling: "any",
        form_factor: "any",
        aesthetics: "简洁",
        noise: "均衡",
        upgrade: "保留升级空间",
        existing_parts: [],
      },
      messages: [],
    };
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      requests.push({ url, init });
      if (url.endsWith("/api/conversations") && init?.method === "POST")
        return Promise.resolve(new Response(JSON.stringify(conversation), { status: 200 }));
      if (url.endsWith("/api/conversations/conversation-auto-generate/messages"))
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...conversation,
              messages: [
                { role: "user", content: "预算 8000 元玩战争雷霆", created_at: new Date().toISOString() },
              ],
            }),
            { status: 200 },
          ),
        );
      if (url.endsWith("/api/conversations/conversation-auto-generate/profile"))
        return Promise.resolve(new Response(JSON.stringify(conversation), { status: 200 }));
      if (url.includes("/api/plans/generate?conversation_id=conversation-auto-generate"))
        return Promise.reject(new Error("worker offline"));
      return Promise.reject(new Error(`unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await waitFor(() => expect(screen.getByText("API 已连接")).toBeTruthy());

    const input = screen.getByLabelText("输入你的装机需求");
    fireEvent.change(input, { target: { value: "预算 8000 元玩战争雷霆" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(
      () => expect(screen.getByText("三套方案已生成（本地演示）")).toBeTruthy(),
      { timeout: 3000 },
    );
    const profileRequest = requests.find((request) => request.url.endsWith("/profile"));
    expect(profileRequest).toBeTruthy();
    expect(JSON.parse(String(profileRequest?.init?.body)).profile.budget).toBe(8000);
    expect(screen.getAllByText(/War Thunder/).length).toBeGreaterThan(0);
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
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /War Thunder/ })).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: /War Thunder/ }));
    await waitFor(() =>
      expect(screen.getByText("95 GB 可用空间")).toBeTruthy(),
    );
  });

  it("opens hardware details from the ladder and supports selecting a candidate", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "硬件天梯" }));
    const ladderName = await screen.findByText("GeForce RTX 4070 SUPER");
    fireEvent.click(ladderName.closest("button")!);
    expect(
      await screen.findByRole("dialog", { name: "选择显卡" }),
    ).toBeTruthy();
    expect(screen.getByText("配件详情")).toBeTruthy();
    expect(screen.getByRole("button", { name: "使用此显卡" })).toBeTruthy();
  });

  it("opens replacement from the part name and continues to product details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    fireEvent.click(
      screen.getByRole("button", { name: /更换显卡：GeForce RTX 4070 SUPER/ }),
    );
    expect(
      await screen.findByRole("dialog", { name: "选择显卡" }),
    ).toBeTruthy();
    expect(screen.getAllByText(/GeForce RTX/).length).toBeGreaterThan(5);
    fireEvent.click(screen.getByRole("button", { name: "商品详情" }));
    expect(await screen.findByRole("main", { name: /商品详情/ })).toBeTruthy();
    expect(screen.getByText("京东与拼多多")).toBeTruthy();
    expect(screen.getByText("逐项参数")).toBeTruthy();
    expect(screen.getByRole("button", { name: "使用此显卡" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "返回选配" }));
    expect(screen.getByRole("dialog", { name: "选择显卡" })).toBeTruthy();
  });

  it("keeps the latest candidate offer when product responses finish out of order", async () => {
    const conversation = {
      id: "conversation-race",
      profile: {
        budget: 8000,
        use_case: "游戏与日常",
        resolution: "2K",
        refresh_rate: 165,
        cpu_brand: "any",
        gpu_brand: "any",
        cooling: "any",
        form_factor: "any",
        aesthetics: "简洁",
        noise: "均衡",
        upgrade: "保留升级空间",
        existing_parts: [],
      },
      messages: [],
    };
    const items = [
      {
        id: "part-a",
        category: "gpu",
        name: "候选 A",
        brand: "厂商 A",
        price: 3000,
        source: "目录",
        specs: { vram_gb: 12, memory_type: "GDDR6" },
        power_w: 200,
      },
      {
        id: "part-b",
        category: "gpu",
        name: "候选 B",
        brand: "厂商 B",
        price: 3500,
        source: "目录",
        specs: { vram_gb: 16, memory_type: "GDDR6" },
        power_w: 220,
      },
    ];
    const catalog = {
      items,
      total: items.length,
      facets: { brands: [], kinds: [], price_min: 3000, price_max: 3500 },
      sync: {
        enabled: true,
        status: "completed",
        provider: "测试目录",
        item_count: 2,
        message: "已更新",
        stale: false,
      },
    };
    const offer = (partId: string, seller: string, price: number) => ({
      part_id: partId,
      platform: "jd",
      price,
      landed_price: price,
      source: "测试报价",
      seller,
      status: "实时读取",
      captured_at: "2026-08-31T10:00:00+08:00",
      url: "https://example.invalid/product",
      is_live: true,
    });
    const detail = (partId: string, seller: string, price: number) => ({
      part: items.find((item) => item.id === partId),
      offers: [offer(partId, seller, price)],
      evidence: [],
      sources: [],
    });
    let productACalled = false;
    let productBCalled = false;
    let resolveA: ((response: Response) => void) | undefined;
    let resolveB: ((response: Response) => void) | undefined;
    const productA = new Promise<Response>((resolve) => {
      resolveA = resolve;
    });
    const productB = new Promise<Response>((resolve) => {
      resolveB = resolve;
    });
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/conversations") && init?.method === "POST")
        return Promise.resolve(
          new Response(JSON.stringify(conversation), { status: 200 }),
        );
      if (url.endsWith("/api/catalog/gpu"))
        return Promise.resolve(
          new Response(JSON.stringify(catalog), { status: 200 }),
        );
      if (url.endsWith("/api/products/demo-gpu"))
        return Promise.reject(new Error("demo product is local only"));
      if (url.endsWith("/api/products/part-a")) {
        productACalled = true;
        return productA;
      }
      if (url.endsWith("/api/products/part-b")) {
        productBCalled = true;
        return productB;
      }
      return Promise.reject(new Error(`unexpected request: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await waitFor(() => expect(screen.getByText("API 已连接")).toBeTruthy());
    fireEvent.click(
      screen.getByRole("button", { name: /更换显卡：GeForce RTX 4070 SUPER/ }),
    );
    await screen.findByRole("dialog", { name: "选择显卡" });
    await waitFor(() => expect(productACalled).toBe(true));
    fireEvent.click(screen.getByText("候选 B").closest("button")!);
    await waitFor(() => expect(productBCalled).toBe(true));
    resolveB!(
      new Response(JSON.stringify(detail("part-b", "B 平台店铺", 2222)), {
        status: 200,
      }),
    );
    expect(await screen.findByText("B 平台店铺")).toBeTruthy();
    resolveA!(
      new Response(JSON.stringify(detail("part-a", "A 平台店铺", 1111)), {
        status: 200,
      }),
    );
    await new Promise((resolve) => window.setTimeout(resolve, 30));
    expect(screen.queryByText("A 平台店铺")).toBeNull();
    expect(screen.getByText("B 平台店铺")).toBeTruthy();
  });

  it("does not request an export for a demo plan after the API connects", async () => {
    const conversation = {
      id: "conversation-test",
      profile: {
        budget: 8000,
        use_case: "游戏与日常",
        resolution: "2K",
        refresh_rate: 165,
        cpu_brand: "any",
        gpu_brand: "any",
        cooling: "any",
        form_factor: "any",
        aesthetics: "简洁",
        noise: "均衡",
        upgrade: "保留升级空间",
        existing_parts: [],
      },
      messages: [
        {
          role: "assistant",
          content: "你好",
          created_at: new Date().toISOString(),
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(conversation), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockRejectedValue(new Error("unexpected request"));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await waitFor(() => expect(screen.getByText("API 已连接")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /导出清单/ }));
    expect(screen.getByText(/当前是演示预览/)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
