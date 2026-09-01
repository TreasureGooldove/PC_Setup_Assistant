import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { Offer } from "../../types";
import { OfferComparison } from "./OfferComparison";

const offers: Offer[] = [
  {
    part_id: "gpu-test",
    platform: "jd",
    price: 4999,
    list_price: 5299,
    landed_price: 4899,
    source: "京东公开页",
    seller: "显卡京东自营店",
    status: "结构化参考",
    captured_at: "2026-08-31T10:00:00+08:00",
    url: "https://search.jd.com/Search?keyword=gpu-test",
    is_live: true,
  },
  {
    part_id: "gpu-test",
    platform: "pdd",
    price: 4799,
    landed_price: 4699,
    source: "拼多多示例报价",
    seller: "显卡授权店",
    status: "示例报价（未联网）",
    captured_at: "2026-08-31T10:00:00+08:00",
    url: "https://mobile.yangkeduo.com/search_result.html?search_key=gpu-test",
    is_live: false,
  },
];

afterEach(cleanup);

describe("OfferComparison", () => {
  it("renders platform, price, seller, status, capture time, and links", () => {
    render(<OfferComparison offers={offers} />);

    expect(screen.getByText("京东")).toBeTruthy();
    expect(screen.getByText("拼多多")).toBeTruthy();
    expect(screen.getByText("¥4,899")).toBeTruthy();
    expect(screen.getByText("¥4,699")).toBeTruthy();
    expect(screen.getByText("显卡京东自营店")).toBeTruthy();
    expect(screen.getByText("显卡授权店")).toBeTruthy();
    expect(screen.getByText("结构化参考")).toBeTruthy();
    expect(screen.getByText("示例报价（未联网）")).toBeTruthy();
    expect(screen.getAllByRole("link", { name: /前往平台核价/ })).toHaveLength(2);
  });

  it("announces loading instead of stale offer cards", () => {
    render(<OfferComparison offers={[]} loading compact />);
    expect(screen.getByText(/正在读取该型号的平台报价/)).toBeTruthy();
    expect(screen.getByRole("region", { name: "平台报价" })).toBeTruthy();
  });

  it("keeps an unconfigured platform price visibly pending", () => {
    render(
      <OfferComparison
        offers={[
          {
            part_id: "gpu-pending",
            platform: "jd",
            source: "京东平台搜索入口",
            status: "待联网",
            url: "https://search.jd.com/Search?keyword=gpu-pending",
            is_live: false,
          },
        ]}
      />,
    );

    expect(screen.getAllByText("待联网").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("当前未取得金额")).toBeTruthy();
    expect(screen.getByText("店铺信息待取得")).toBeTruthy();
    expect(screen.queryByText(/¥0/)).toBeNull();
  });
});
