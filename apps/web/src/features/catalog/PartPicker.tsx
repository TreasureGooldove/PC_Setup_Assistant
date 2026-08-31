import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ExternalLink,
  Search,
  ShoppingBag,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { Part, PartCategory } from "../../types";
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
  onClose: () => void;
  onUse: (part: Part) => void | Promise<void>;
  onViewDetails: (part: Part) => void;
}

export function PartPicker({
  slot,
  items,
  initialPartId,
  busy = false,
  onClose,
  onUse,
  onViewDetails,
}: PartPickerProps) {
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("all");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
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

  const brands = useMemo(
    () => Array.from(new Set(items.map((item) => item.brand))).sort(),
    [items],
  );
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const low = minPrice ? Number(minPrice) : undefined;
    const high = maxPrice ? Number(maxPrice) : undefined;
    return items.filter((item) => {
      if (
        needle &&
        !`${item.name} ${item.brand} ${item.summary ?? ""}`
          .toLowerCase()
          .includes(needle)
      )
        return false;
      if (brand !== "all" && item.brand !== brand) return false;
      if (low !== undefined && item.price < low) return false;
      if (high !== undefined && item.price > high) return false;
      return true;
    });
  }, [brand, items, maxPrice, minPrice, query]);
  const selected = items.find((item) => item.id === selectedId) ?? filtered[0];

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
            <p>先筛选候选，再查看规格、参考排名和注意事项。</p>
          </div>
          <button
            className="icon-button"
            type="button"
            aria-label="关闭配件选择"
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </header>
        <div className="picker-filters">
          <label className="picker-search">
            <Search size={16} />
            <input
              aria-label="搜索配件"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={`搜索${SLOT_LABELS[slot]}型号`}
            />
          </label>
          <label>
            <span>品牌</span>
            <select
              aria-label="品牌筛选"
              value={brand}
              onChange={(event) => setBrand(event.target.value)}
            >
              <option value="all">全部品牌</option>
              {brands.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>最低价</span>
            <input
              aria-label="最低价格"
              inputMode="numeric"
              value={minPrice}
              onChange={(event) =>
                setMinPrice(event.target.value.replace(/\D/g, ""))
              }
              placeholder="不限"
            />
          </label>
          <label>
            <span>最高价</span>
            <input
              aria-label="最高价格"
              inputMode="numeric"
              value={maxPrice}
              onChange={(event) =>
                setMaxPrice(event.target.value.replace(/\D/g, ""))
              }
              placeholder="不限"
            />
          </label>
        </div>
        <div className="picker-body">
          <div className="picker-results" aria-label="配件搜索结果">
            <div className="picker-result-meta">
              <strong>{filtered.length}</strong> 个候选
            </div>
            {filtered.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`picker-result ${selected?.id === item.id ? "selected" : ""}`}
                onClick={() => setSelectedId(item.id)}
              >
                <span>
                  <strong>{item.name}</strong>
                  <small>
                    {item.brand} · {item.power_w || 0}W
                  </small>
                </span>
                <b>¥{formatMoney(item.price)}</b>
              </button>
            ))}
            {!filtered.length && (
              <div className="picker-empty">
                没有符合条件的配件，请放宽筛选条件。
              </div>
            )}
          </div>
          <div className="picker-detail">
            {selected ? (
              <>
                <div className="part-detail-title">
                  <div>
                    <span className="eyebrow">配件详情</span>
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
                    <strong>
                      {selected.rank ? `#${selected.rank}` : "待确认"}
                    </strong>
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
                    <BarChart3 size={17} />
                    <strong>辅助点评</strong>
                  </div>
                  {(selected.advantages ?? []).map((text) => (
                    <div className="review-line advantage" key={text}>
                      <CheckCircle2 size={16} />
                      <span>{text}</span>
                    </div>
                  ))}
                  {(selected.cautions ?? []).map((text) => (
                    <div className="review-line caution" key={text}>
                      <AlertTriangle size={16} />
                      <span>{text}</span>
                    </div>
                  ))}
                  {!(
                    selected.advantages?.length || selected.cautions?.length
                  ) && (
                    <div className="review-line caution">
                      <AlertTriangle size={16} />
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
                      <ExternalLink size={13} />
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
              <ShoppingBag size={16} />
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
