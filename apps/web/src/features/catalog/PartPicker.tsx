import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ExternalLink,
  ImageIcon,
  RotateCw,
  Search,
  ShoppingBag,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import type { CatalogSyncStatus, Part, PartCategory } from "../../types";
import {
  formatMoney,
  formatSpec,
  SLOT_LABELS,
  SPEC_LABELS,
} from "./partFormat";

interface PartPickerProps {
  slot: PartCategory;
  items: Part[];
  initialPartId?: string;
  busy?: boolean;
  sync?: CatalogSyncStatus | null;
  syncProgress?: number;
  onClose: () => void;
  onUse: (part: Part) => void | Promise<void>;
  onViewDetails: (part: Part) => void;
  onRefresh?: () => void | Promise<void>;
}

function itemKind(slot: PartCategory, item: Part): string {
  const explicit = item.specs.catalog_kind;
  if (typeof explicit === "string" && explicit) return explicit;
  const name = item.name.toUpperCase();
  if (slot === "gpu") {
    const match = name.match(
      /(RTX\s*\d{4}(?:\s*TI|\s*SUPER)?|RX\s*\d{4}(?:\s*XTX|\s*XT|\s*GRE)?)/,
    );
    return (
      match?.[1]
        ?.replace(/\s+/g, " ")
        .replace("TI", "Ti")
        .replace("SUPER", "SUPER") ?? "其他型号"
    );
  }
  if (slot === "cpu") {
    return (
      name.match(/RYZEN\s*[579]|CORE\s*ULTRA|CORE\s*I[3579]/)?.[0] ??
      "其他系列"
    )
      .replace("RYZEN", "Ryzen")
      .replace("CORE", "Core");
  }
  if (slot === "cooling")
    return item.specs.type === "water" ? "水冷散热器" : "风冷散热器";
  if (slot === "memory") return String(item.specs.memory_type ?? "其他内存");
  if (slot === "psu")
    return item.specs.wattage ? `${item.specs.wattage}W` : "其他功率";
  if (slot === "case" || slot === "motherboard")
    return String(item.specs.form_factor ?? "其他尺寸");
  if (slot === "storage") {
    const capacity = Number(item.specs.capacity_gb ?? 0);
    return capacity >= 1024 ? `${capacity / 1024}TB` : `${capacity || "其他"}GB`;
  }
  return "其他";
}

function itemSpecSummary(slot: PartCategory, item: Part): string {
  const preferred: Record<PartCategory, string[]> = {
    cpu: ["cores_threads", "architecture", "socket"],
    motherboard: ["chipset", "socket", "form_factor"],
    gpu: ["vram_gb", "memory_type", "memory_bus_bit"],
    memory: ["capacity_gb", "memory_type", "speed_mts"],
    storage: ["capacity_gb", "interface", "connector"],
    psu: ["wattage", "rating", "modular"],
    cooling: ["type", "radiator_mm", "height_mm"],
    case: ["form_factor", "gpu_length_mm", "radiator_mm"],
  };
  const values = preferred[slot]
    .filter((key) => item.specs[key] !== undefined && item.specs[key] !== null)
    .slice(0, 3)
    .map((key) => `${SPEC_LABELS[key] ?? key} ${formatSpec(key, item.specs[key])}`);
  return values.join(" · ") || item.summary || `${item.brand} 产品候选`;
}

export function PartPicker({
  slot,
  items,
  initialPartId,
  busy = false,
  sync,
  syncProgress = 0,
  onClose,
  onUse,
  onViewDetails,
  onRefresh,
}: PartPickerProps) {
  const [queryDraft, setQueryDraft] = useState("");
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("all");
  const [kind, setKind] = useState("all");
  const [minPriceDraft, setMinPriceDraft] = useState("");
  const [maxPriceDraft, setMaxPriceDraft] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sort, setSort] = useState("default");
  const [selectedId, setSelectedId] = useState(
    initialPartId ?? items[0]?.id ?? "",
  );

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  useEffect(() => {
    if (!items.some((item) => item.id === selectedId)) {
      setSelectedId(
        initialPartId && items.some((item) => item.id === initialPartId)
          ? initialPartId
          : (items[0]?.id ?? ""),
      );
    }
  }, [initialPartId, items, selectedId]);

  const brands = useMemo(() => {
    const counts = new Map<string, number>();
    items.forEach((item) => counts.set(item.brand, (counts.get(item.brand) ?? 0) + 1));
    return [...counts.entries()].sort(
      ([left, leftCount], [right, rightCount]) =>
        rightCount - leftCount || left.localeCompare(right, "zh-CN"),
    );
  }, [items]);
  const kinds = useMemo(() => {
    const counts = new Map<string, number>();
    items.forEach((item) => {
      const value = itemKind(slot, item);
      counts.set(value, (counts.get(value) ?? 0) + 1);
    });
    return [...counts.entries()].sort(
      ([left, leftCount], [right, rightCount]) =>
        rightCount - leftCount || left.localeCompare(right, "zh-CN"),
    );
  }, [items, slot]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const low = minPrice ? Number(minPrice) : undefined;
    const high = maxPrice ? Number(maxPrice) : undefined;
    const result = items.filter((item) => {
      if (
        needle &&
        !`${item.name} ${item.brand} ${item.summary ?? ""}`
          .toLowerCase()
          .includes(needle)
      )
        return false;
      if (brand !== "all" && item.brand !== brand) return false;
      if (kind !== "all" && itemKind(slot, item) !== kind) return false;
      if (low !== undefined && item.price < low) return false;
      if (high !== undefined && item.price > high) return false;
      return true;
    });
    if (sort === "price_asc") result.sort((left, right) => left.price - right.price);
    if (sort === "price_desc") result.sort((left, right) => right.price - left.price);
    if (sort === "brand")
      result.sort(
        (left, right) =>
          left.brand.localeCompare(right.brand, "zh-CN") || left.price - right.price,
      );
    return result;
  }, [brand, items, kind, maxPrice, minPrice, query, slot, sort]);
  const selected =
    filtered.find((item) => item.id === selectedId) ?? filtered[0] ?? null;
  const syncing = sync?.status === "queued" || sync?.status === "running";

  function applySearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(queryDraft.trim());
    setMinPrice(minPriceDraft);
    setMaxPrice(maxPriceDraft);
  }

  function clearFilters() {
    setQueryDraft("");
    setQuery("");
    setBrand("all");
    setKind("all");
    setMinPriceDraft("");
    setMaxPriceDraft("");
    setMinPrice("");
    setMaxPrice("");
    setSort("default");
  }

  return (
    <div
      className="picker-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="part-picker"
        role="dialog"
        aria-modal="true"
        aria-label={`选择${SLOT_LABELS[slot]}`}
      >
        <header className="picker-head">
          <div>
            <span className="eyebrow">手动选配</span>
            <h2>选择{SLOT_LABELS[slot]}</h2>
            <p>按厂商、型号系列和价格筛选，选择后会重新执行装机检查。</p>
          </div>
          <button
            className="icon-button"
            type="button"
            aria-label="关闭配件选择"
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="picker-filters">
          <form className="picker-search-form" onSubmit={applySearch}>
            <label className="picker-search">
              <span>型号或厂商</span>
              <div>
                <Search size={17} aria-hidden="true" />
                <input
                  aria-label="搜索配件"
                  value={queryDraft}
                  onChange={(event) => setQueryDraft(event.target.value)}
                  placeholder={`搜索${SLOT_LABELS[slot]}型号或厂商`}
                />
              </div>
            </label>
            <label className="picker-price-field">
              <span>最低价</span>
              <input
                aria-label="最低价格"
                inputMode="numeric"
                value={minPriceDraft}
                onChange={(event) =>
                  setMinPriceDraft(event.target.value.replace(/\D/g, ""))
                }
                placeholder="¥ 不限"
              />
            </label>
            <label className="picker-price-field">
              <span>最高价</span>
              <input
                aria-label="最高价格"
                inputMode="numeric"
                value={maxPriceDraft}
                onChange={(event) =>
                  setMaxPriceDraft(event.target.value.replace(/\D/g, ""))
                }
                placeholder="¥ 不限"
              />
            </label>
            <button className="picker-search-button" type="submit">
              <Search size={16} aria-hidden="true" />
              搜索
            </button>
          </form>

          <div className="picker-filter-line">
            <span className="filter-line-label">型号</span>
            <div className="filter-chip-row" aria-label="型号类型筛选">
              <button
                type="button"
                className={kind === "all" ? "active" : ""}
                aria-pressed={kind === "all"}
                onClick={() => setKind("all")}
              >
                全部 <small>{items.length}</small>
              </button>
              {kinds.map(([value, count]) => (
                <button
                  type="button"
                  key={value}
                  className={kind === value ? "active" : ""}
                  aria-pressed={kind === value}
                  onClick={() => setKind(value)}
                >
                  {value} <small>{count}</small>
                </button>
              ))}
            </div>
          </div>
          <div className="picker-filter-line">
            <span className="filter-line-label">厂商</span>
            <div className="filter-chip-row" aria-label="厂商品牌筛选">
              <button
                type="button"
                className={brand === "all" ? "active" : ""}
                aria-pressed={brand === "all"}
                onClick={() => setBrand("all")}
              >
                全部品牌
              </button>
              {brands.map(([value, count]) => (
                <button
                  type="button"
                  key={value}
                  className={brand === value ? "active" : ""}
                  aria-pressed={brand === value}
                  onClick={() => setBrand(value)}
                >
                  {value} <small>{count}</small>
                </button>
              ))}
            </div>
          </div>
          <div className="picker-catalog-status" aria-live="polite">
            <div>
              <RotateCw
                size={15}
                className={syncing ? "spin" : ""}
                aria-hidden="true"
              />
              <span>
                <strong>{sync?.provider ?? "本地结构化目录"}</strong>
                {" · "}
                {sync?.message ?? "正在读取候选"}
                {sync?.updated_at
                  ? ` · ${new Date(sync.updated_at).toLocaleString("zh-CN")}`
                  : ""}
              </span>
            </div>
            <div className="picker-status-actions">
              <label>
                <span>排序</span>
                <select
                  aria-label="候选排序"
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                >
                  <option value="default">综合排序</option>
                  <option value="price_asc">价格从低到高</option>
                  <option value="price_desc">价格从高到低</option>
                  <option value="brand">按厂商排序</option>
                </select>
              </label>
              <button type="button" className="text-button" onClick={clearFilters}>
                <SlidersHorizontal size={14} aria-hidden="true" />
                清空筛选
              </button>
              {onRefresh && sync?.enabled !== false ? (
                <button
                  type="button"
                  className="text-button"
                  disabled={syncing}
                  onClick={() => void onRefresh()}
                >
                  <RotateCw size={14} aria-hidden="true" />
                  {syncing ? "更新中" : "更新候选"}
                </button>
              ) : null}
            </div>
            {syncing ? (
              <div className="catalog-progress" aria-label={`目录更新 ${syncProgress}%`}>
                <span style={{ width: `${Math.max(6, syncProgress)}%` }} />
              </div>
            ) : null}
          </div>
        </div>

        <div className="picker-body">
          <div className="picker-results" aria-label="配件搜索结果">
            <div className="picker-result-meta">
              <span>
                <strong>{filtered.length}</strong> 个候选
              </span>
              <small>价格均为参考价</small>
            </div>
            {filtered.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`picker-result ${selected?.id === item.id ? "selected" : ""}`}
                aria-pressed={selected?.id === item.id}
                onClick={() => setSelectedId(item.id)}
              >
                <span className="picker-product-image" aria-hidden="true">
                  <ImageIcon size={22} />
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt=""
                      width="76"
                      height="58"
                      loading="lazy"
                      referrerPolicy="no-referrer"
                      onError={(event) => {
                        event.currentTarget.style.opacity = "0";
                      }}
                    />
                  ) : null}
                </span>
                <span className="picker-product-copy">
                  <small className="picker-product-brand">{item.brand}</small>
                  <strong>{item.name}</strong>
                  <small>{itemSpecSummary(slot, item)}</small>
                  <em>
                    {item.source}
                    {item.data_updated_at ? ` · ${item.data_updated_at}` : ""}
                  </em>
                </span>
                <span className="picker-product-price">
                  <b>¥{formatMoney(item.price)}</b>
                  <small>参考价</small>
                </span>
              </button>
            ))}
            {!filtered.length && (
              <div className="picker-empty">
                没有符合条件的产品，请清空厂商或放宽价格区间。
              </div>
            )}
          </div>
          <div className="picker-detail">
            {selected ? (
              <>
                <div className="part-detail-title">
                  <div>
                    <span className="eyebrow">
                      <span>配件详情</span>
                      <em> · {selected.brand}</em>
                    </span>
                    <h3>{selected.name}</h3>
                    <p>
                      {selected.summary ||
                        "当前为结构化参考数据，缺失字段会标记为待确认。"}
                    </p>
                  </div>
                  <strong>¥{formatMoney(selected.price)}</strong>
                </div>
                <div className="insight-metrics">
                  <div>
                    <span>参考排名</span>
                    <strong>{selected.rank ? `#${selected.rank}` : "待确认"}</strong>
                  </div>
                  <div>
                    <span>参考跑分</span>
                    <strong>
                      {selected.benchmark_score
                        ? formatMoney(selected.benchmark_score)
                        : "待确认"}
                    </strong>
                  </div>
                  <div>
                    <span>参考百分位</span>
                    <strong>
                      {selected.percentile !== null &&
                      selected.percentile !== undefined
                        ? `${selected.percentile.toFixed(2)}%`
                        : "待确认"}
                    </strong>
                  </div>
                </div>
                <div className="spec-chip-grid">
                  {Object.entries(selected.specs)
                    .filter(([key]) => key !== "catalog_kind")
                    .slice(0, 14)
                    .map(([key, value]) => (
                      <div key={key}>
                        <span>{SPEC_LABELS[key] ?? key}</span>
                        <strong>{formatSpec(key, value)}</strong>
                      </div>
                    ))}
                </div>
                <section className="ai-review" aria-label="辅助点评">
                  <div className="review-title">
                    <BarChart3 size={17} aria-hidden="true" />
                    <strong>辅助点评</strong>
                  </div>
                  {(selected.advantages ?? []).map((text) => (
                    <div className="review-line advantage" key={text}>
                      <CheckCircle2 size={16} aria-hidden="true" />
                      <span>{text}</span>
                    </div>
                  ))}
                  {(selected.cautions ?? []).map((text) => (
                    <div className="review-line caution" key={text}>
                      <AlertTriangle size={16} aria-hidden="true" />
                      <span>{text}</span>
                    </div>
                  ))}
                  {!(selected.advantages?.length || selected.cautions?.length) && (
                    <div className="review-line caution">
                      <AlertTriangle size={16} aria-hidden="true" />
                      <span>
                        该配件暂缺结构化点评，使用后仍会执行兼容性硬规则检查。
                      </span>
                    </div>
                  )}
                </section>
                <div className="source-line">
                  <span>
                    来源：{selected.source}
                    {selected.data_updated_at
                      ? ` · 更新 ${selected.data_updated_at}`
                      : ""}
                  </span>
                  {selected.url ? (
                    <a href={selected.url} target="_blank" rel="noreferrer">
                      查看规格来源
                      <ExternalLink size={13} aria-hidden="true" />
                    </a>
                  ) : null}
                </div>
              </>
            ) : (
              <div className="picker-empty">请选择一个候选配件。</div>
            )}
          </div>
        </div>
        <footer className="picker-actions">
          <span>使用后会重新计算总价、功耗与兼容性。</span>
          <div className="picker-action-buttons">
            <button
              className="glass-button"
              type="button"
              disabled={!selected || busy}
              onClick={() => selected && onViewDetails(selected)}
            >
              <ShoppingBag size={16} aria-hidden="true" />
              商品详情
            </button>
            <button
              className="gold-button"
              type="button"
              disabled={!selected || busy}
              onClick={() => selected && onUse(selected)}
            >
              {busy ? "正在应用…" : `使用此${SLOT_LABELS[slot]}`}
            </button>
          </div>
        </footer>
      </section>
    </div>
  );
}
