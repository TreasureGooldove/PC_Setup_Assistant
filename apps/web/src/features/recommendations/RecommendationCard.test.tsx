import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RecommendationCard } from "./RecommendationCard";
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
  id: "demo-balanced",
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
        id: "cpu-test",
        category: "cpu",
        name: "Ryzen 7 7700",
        brand: "AMD",
        price: 1599,
        source: "Fixture参考价",
        specs: { socket: "AM5" },
        power_w: 65,
      },
      reason: "满足游戏与日常多任务。",
      locked: false,
    },
  ],
  compatibility: [],
  created_at: "2026-08-31T00:00:00Z",
};

describe("RecommendationCard", () => {
  it("shows an auditable structured recommendation", () => {
    const recommendation = createOfflineRecommendation(plan, profile, null);
    render(
      <RecommendationCard
        recommendation={recommendation}
        plan={plan}
        profile={profile}
        loading={false}
        error=""
        progress={100}
        message="已完成"
        onGenerate={vi.fn()}
        onRegenerate={vi.fn()}
        onOpenGame={vi.fn()}
      />,
    );

    expect(screen.getByText("为什么这样选")).toBeTruthy();
    expect(screen.getAllByText("Ryzen 7 7700").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("查看依据与来源（4）")).toBeTruthy();
    expect(screen.getByText("参考金额")).toBeTruthy();
  });

  it("shows progress and supports retry from an error state", () => {
    const onGenerate = vi.fn();
    const { rerender } = render(
      <RecommendationCard
        recommendation={null}
        plan={plan}
        profile={profile}
        loading
        error=""
        progress={55}
        message="汇总兼容性依据"
        onGenerate={onGenerate}
        onRegenerate={vi.fn()}
        onOpenGame={vi.fn()}
      />,
    );
    expect(screen.getByRole("progressbar", { name: "建议生成进度 55%" })).toBeTruthy();
    expect(screen.getByText("汇总兼容性依据")).toBeTruthy();

    rerender(
      <RecommendationCard
        recommendation={null}
        plan={plan}
        profile={profile}
        loading={false}
        error="Worker 尚未启动"
        progress={55}
        message="汇总兼容性依据"
        onGenerate={onGenerate}
        onRegenerate={vi.fn()}
        onOpenGame={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "重试" }));
    expect(onGenerate).toHaveBeenCalledOnce();
  });
});
