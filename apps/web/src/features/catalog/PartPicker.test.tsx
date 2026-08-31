import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CatalogSyncStatus, Part } from "../../types";
import { PartPicker } from "./PartPicker";

const items: Part[] = [
  {
    id: "asus-5070",
    category: "gpu",
    name: "TUF RTX 5070 O12G GAMING",
    brand: "华硕 ASUS",
    price: 7699,
    source: "ZOL 公开产品目录",
    image_url: "https://example.invalid/asus.jpg",
    specs: {
      catalog_kind: "RTX 5070",
      vram_gb: 12,
      memory_type: "GDDR7",
      memory_bus_bit: 192,
    },
    power_w: 250,
    data_updated_at: "2026-08-31",
  },
  {
    id: "asus-5060ti",
    category: "gpu",
    name: "TUF RTX 5060 Ti O16G GAMING",
    brand: "华硕 ASUS",
    price: 6699,
    source: "Fixture参考价",
    specs: {
      catalog_kind: "RTX 5060 Ti",
      vram_gb: 16,
      memory_type: "GDDR7",
      memory_bus_bit: 128,
    },
    power_w: 180,
  },
  {
    id: "msi-5070",
    category: "gpu",
    name: "RTX 5070 GAMING TRIO OC 12G",
    brand: "微星 MSI",
    price: 6899,
    source: "Fixture参考价",
    specs: {
      catalog_kind: "RTX 5070",
      vram_gb: 12,
      memory_type: "GDDR7",
      memory_bus_bit: 192,
    },
    power_w: 250,
  },
];

const sync: CatalogSyncStatus = {
  enabled: true,
  status: "completed",
  provider: "ZOL 公开产品目录",
  item_count: 3,
  message: "已更新 3 个公开厂商型号",
  updated_at: "2026-08-31T10:00:00+08:00",
  stale: false,
};

afterEach(cleanup);

describe("PartPicker", () => {
  it("filters concrete vendor models by brand, series and submitted price range", () => {
    render(
      <PartPicker
        slot="gpu"
        items={items}
        sync={sync}
        onClose={vi.fn()}
        onUse={vi.fn()}
        onViewDetails={vi.fn()}
      />,
    );

    const results = screen.getByLabelText("配件搜索结果");
    expect(within(results).getAllByRole("button")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: /华硕 ASUS 2/ }));
    fireEvent.click(screen.getByRole("button", { name: /RTX 5070 2/ }));
    expect(within(results).getAllByRole("button")).toHaveLength(1);
    expect(within(results).getByText("TUF RTX 5070 O12G GAMING")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("最高价格"), {
      target: { value: "7000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "搜索" }));
    expect(within(results).queryByRole("button")).toBeNull();
    expect(screen.getByText(/放宽价格区间/)).toBeTruthy();
  });

  it("shows catalog status and allows a manual refresh", () => {
    const onRefresh = vi.fn();
    render(
      <PartPicker
        slot="gpu"
        items={items}
        sync={sync}
        onClose={vi.fn()}
        onUse={vi.fn()}
        onViewDetails={vi.fn()}
        onRefresh={onRefresh}
      />,
    );
    expect(screen.getAllByText(/已更新 3 个公开厂商型号/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "更新候选" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
