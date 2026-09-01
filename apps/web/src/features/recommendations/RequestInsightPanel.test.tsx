import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RequestInsightPanel } from "./RequestInsightPanel";
import { createOfflineRecommendation } from "./offlineRecommendation";
import type { BuildPlan, NeedProfile } from "../../types";

const profile: NeedProfile = {
  budget: 8000,
  use_case: "游戏与日常",
  resolution: "2K",
  refresh_rate: 165,
  cpu_brand: "any",
  gpu_brand: "any",
  cooling: "air",
  form_factor: "mATX",
  aesthetics: "简洁",
  noise: "均衡",
  upgrade: "保留升级空间",
  existing_parts: [],
};

const plan: BuildPlan = {
  id: "demo-insight",
  style: "balanced",
  title: "均衡耐用",
  summary: "在性能、噪声和升级空间之间保持平衡。",
  budget: 8000,
  total_price: 7200,
  estimated_power_w: 430,
  performance_score: 83,
  items: [
    {
      slot: "cpu",
      part: {
        id: "cpu-insight",
        category: "cpu",
        name: "Ryzen 7 7700",
        brand: "AMD",
        price: 1599,
        source: "Fixture参考价",
        specs: { socket: "AM5" },
        power_w: 65,
      },
      locked: false,
      reason: "满足游戏与日常多任务。",
    },
  ],
  compatibility: [],
  created_at: "2026-09-01T00:00:00Z",
};

const props = {
  profile,
  gameRequirement: null,
  plan,
  busy: false,
  planBusy: false,
  progress: 0,
  message: "",
  error: "",
  onGenerate: vi.fn(),
  onViewResult: vi.fn(),
};

describe("RequestInsightPanel", () => {
  it("shows auditable stages without hidden model reasoning", () => {
    render(
      <RequestInsightPanel
        {...props}
        recommendation={createOfflineRecommendation(plan, profile, null)}
      />,
    );

    expect(screen.getByRole("region", { name: "AI 工作摘要" })).toBeTruthy();
    expect(screen.getByText("结构化结果")).toBeTruthy();
    expect(screen.getByText("本地可复现")).toBeTruthy();
    expect(screen.getByText(/不展示模型内部隐式推理或原始工具日志/)).toBeTruthy();
    expect(screen.getAllByText("已完成").length).toBeGreaterThan(0);
  });

  it("lets the user start generation from the summary", () => {
    render(<RequestInsightPanel {...props} recommendation={null} />);

    fireEvent.click(screen.getByRole("button", { name: "用当前参数生成" }));

    expect(props.onGenerate).toHaveBeenCalledOnce();
  });
});
