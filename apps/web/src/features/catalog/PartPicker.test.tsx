import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CatalogSyncStatus, Offer, Part } from "../../types";
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

const offers: Offer[] = [
  {
    part_id: "asus-5070",
    platform: "jd",
    price: 7599,
    list_price: 7699,
    landed_price: 7499,
    source: "京东示例报价",
    seller: "华硕京东自营店",
    status: "示例报价（未联网）",
    captured_at: "2026-08-31T10:00:00+08:00",
    url: "https://search.jd.com/Search?keyword=5070",
    is_live: false,
  },
  {
    part_id: "asus-5070",
    platform: "pdd",
    price: 7399,
    list_price: 7699,
    landed_price: 7299,
    source: "拼多多示例报价",
    seller: "华硕授权店铺",
    status: "示例报价（未联网）",
    captured_at: "2026-08-31T10:00:00+08:00",
    url: "https://mobile.yangkeduo.com/search_result.html?search_key=5070",
    is_live: false,
  },
];

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

  it("shows platform offers and all available configuration fields", () => {
    const onSelect = vi.fn();
    render(
      <PartPicker
        slot="gpu"
        items={items}
        offers={offers}
        onSelect={onSelect}
        onClose={vi.fn()}
        onUse={vi.fn()}
        onViewDetails={vi.fn()}
      />,
    );

    expect(screen.getByText("京东与拼多多价格")).toBeTruthy();
    expect(screen.getByText("华硕京东自营店")).toBeTruthy();
    expect(screen.getByText("华硕授权店铺")).toBeTruthy();
    expect(screen.getAllByText("示例报价（未联网）")).toHaveLength(2);
    expect(screen.getByText("完整配置参数")).toBeTruthy();
    expect(screen.getByText("GDDR7")).toBeTruthy();
    expect(screen.getByText("192bit")).toBeTruthy();

    const second = screen.getByText("TUF RTX 5060 Ti O16G GAMING");
    fireEvent.click(second.closest("button")!);
    expect(onSelect).toHaveBeenCalledWith(items[1]);
    expect(screen.getByText("16GB")).toBeTruthy();
  });

  it("refreshes the selected item when filters move the default candidate", async () => {
    const onSelect = vi.fn();
    render(
      <PartPicker
        slot="gpu"
        items={items}
        onSelect={onSelect}
        onClose={vi.fn()}
        onUse={vi.fn()}
        onViewDetails={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("搜索配件"), {
      target: { value: "5060" },
    });
    fireEvent.click(screen.getByRole("button", { name: "搜索" }));

    await waitFor(() => expect(onSelect).toHaveBeenCalledWith(items[1]));
    expect(screen.getByRole("heading", { name: items[1].name })).toBeTruthy();
  });
});
