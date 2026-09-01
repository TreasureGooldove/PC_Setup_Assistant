import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DetailedSpecTable } from "./DetailedSpecTable";
import { getDetailedSpecRows } from "./partFormat";

afterEach(cleanup);

describe("DetailedSpecTable", () => {
  it("renders a complete CPU schema and marks unavailable values", () => {
    render(
      <DetailedSpecTable
        category="cpu"
        specs={{
          brand_name: "Intel",
          model: "Core i5-12600KF",
          cores_threads: "10 核 16 线程",
          base_clock: "3.7GHz",
          boost_clock: "4.9GHz",
          l3_cache: "20MB",
          tdp: 125,
          memory_types: "DDR4 / DDR5",
        }}
      />,
    );

    expect(screen.getByRole("region", { name: "完整配置参数" })).toBeTruthy();
    expect(screen.getByText("核心 / 线程")).toBeTruthy();
    expect(screen.getByText("10 核 16 线程")).toBeTruthy();
    expect(screen.getByText("125W")).toBeTruthy();
    expect(screen.getByText("PCIe 版本")).toBeTruthy();
    expect(screen.getAllByText("待确认").length).toBeGreaterThan(0);
    expect(screen.getByText("已采集")).toBeTruthy();
  });

  it("keeps GPU dimensions, memory and power fields visible", () => {
    const specs = {
      brand_name: "华硕 ASUS",
      model: "TUF RTX 5070 O12G GAMING",
      chipset: "RTX 5070",
      vram_gb: 12,
      memory_type: "GDDR7",
      memory_bus_bit: 192,
      pcie_slot: "PCIe 5.0 x16",
      power_connectors: ["12V-2x6"],
      length_mm: 320,
      power_w: 250,
      jd_显存频率: "28Gbps",
    };
    const rows = getDetailedSpecRows("gpu", specs);

    expect(rows.some((row) => row.key === "memory_bus_bit" && row.available)).toBe(true);
    expect(rows.some((row) => row.key === "power_connectors" && row.available)).toBe(true);
    expect(rows.some((row) => row.key === "length_mm" && row.formatted === "320mm")).toBe(true);

    render(<DetailedSpecTable category="gpu" specs={specs} />);
    expect(screen.getByText("显存位宽")).toBeTruthy();
    expect(screen.getByText("192bit")).toBeTruthy();
    expect(screen.getByText("整卡/参考功耗")).toBeTruthy();
    expect(screen.getByText("250W")).toBeTruthy();
    expect(screen.getByText("商品页 · 显存频率")).toBeTruthy();
    expect(screen.getByText("28Gbps")).toBeTruthy();
  });
});
