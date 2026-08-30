import { AlertTriangle, BarChart3, CheckCircle2, ExternalLink, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { Part, PartCategory } from "../../types";

const SLOT_LABELS: Record<PartCategory, string> = {
  cpu: "处理器",
  motherboard: "主板",
  gpu: "显卡",
  memory: "内存",
  storage: "硬盘",
  psu: "电源",
  cooling: "散热",
  case: "机箱",
};

const SPEC_LABELS: Record<string, string> = {
  socket: "接口",
  tdp: "设计功耗",
  score: "性能指数",
  cores_threads: "核心线程",
  base_clock: "基础频率",
  boost_clock: "加速频率",
  integrated_graphics: "核显",
  l3_cache: "三级缓存",
  process: "制程工艺",
  architecture: "架构",
  memory_types: "内存支持",
  launch_year: "上市年份",
  length_mm: "长度",
  pcie_slot: "总线接口",
  power_connectors: "供电接口",
  memory_type: "内存代际",
  capacity_gb: "容量",
  interface: "接口标准",
  connector: "物理接口",
  wattage: "额定功率",
  rating: "认证等级",
  form_factor: "板型/尺寸",
  max_memory_gb: "最大内存",
  memory_slots: "内存插槽",
  m2_slots: "M.2 插槽",
  sata_ports: "SATA 接口",
  gpu_slot: "显卡插槽",
  type: "散热方式",
  height_mm: "散热高度",
  radiator_mm: "冷排尺寸",
  capacity_w: "解热能力",
  supported_sockets: "支持平台",
  supported_form_factors: "支持板型",
  gpu_length_mm: "显卡限长",
  cooler_height_mm: "风冷限高",
};

function formatMoney(value: number) {
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 }).format(value);
}

function formatSpec(key: string, value: unknown) {
  if (Array.isArray(value)) return value.join("、");
  if (typeof value === "boolean") return value ? "支持" : "不支持";
  if (value === null || value === undefined || value === "") return "待确认";
  if (typeof value === "number") {
    if (["tdp", "capacity_w", "wattage"].includes(key)) return `${value}W`;
    if (["length_mm", "height_mm", "radiator_mm", "gpu_length_mm", "cooler_height_mm"].includes(key)) return `${value}mm`;
    if (["capacity_gb", "max_memory_gb"].includes(key)) return `${value}GB`;
  }
  return String(value);
}

interface PartPickerProps {
  slot: PartCategory;
  items: Part[];
  initialPartId?: string;
  busy?: boolean;
  onClose: () => void;
  onUse: (part: Part) => void | Promise<void>;
}

export function PartPicker({ slot, items, initialPartId, busy = false, onClose, onUse }: PartPickerProps) {
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("all");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [selectedId, setSelectedId] = useState(initialPartId ?? items[0]?.id ?? "");

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  useEffect(() => {
    if (!items.some((item) => item.id === selectedId)) {
      setSelectedId(initialPartId && items.some((item) => item.id === initialPartId) ? initialPartId : items[0]?.id ?? "");
    }
  }, [initialPartId, items, selectedId]);

  const brands = useMemo(() => Array.from(new Set(items.map((item) => item.brand))).sort(), [items]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const low = minPrice ? Number(minPrice) : undefined;
    const high = maxPrice ? Number(maxPrice) : undefined;
    return items.filter((item) => {
      if (needle && !`${item.name} ${item.brand} ${item.summary ?? ""}`.toLowerCase().includes(needle)) return false;
      if (brand !== "all" && item.brand !== brand) return false;
      if (low !== undefined && item.price < low) return false;
      if (high !== undefined && item.price > high) return false;
      return true;
    });
  }, [brand, items, maxPrice, minPrice, query]);
  const selected = items.find((item) => item.id === selectedId) ?? filtered[0];

  return <div className="picker-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="part-picker" role="dialog" aria-modal="true" aria-label={`选择${SLOT_LABELS[slot]}`}>
      <header className="picker-head">
        <div><span className="eyebrow">手动选配</span><h2>选择{SLOT_LABELS[slot]}</h2><p>先筛选候选，再查看规格、参考排名和注意事项。</p></div>
        <button className="icon-button" type="button" aria-label="关闭配件选择" onClick={onClose}><X size={18} /></button>
      </header>
      <div className="picker-filters">
        <label className="picker-search"><Search size={16} /><input aria-label="搜索配件" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`搜索${SLOT_LABELS[slot]}型号`} /></label>
        <label><span>品牌</span><select aria-label="品牌筛选" value={brand} onChange={(event) => setBrand(event.target.value)}><option value="all">全部品牌</option>{brands.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label><span>最低价</span><input aria-label="最低价格" inputMode="numeric" value={minPrice} onChange={(event) => setMinPrice(event.target.value.replace(/\D/g, ""))} placeholder="不限" /></label>
        <label><span>最高价</span><input aria-label="最高价格" inputMode="numeric" value={maxPrice} onChange={(event) => setMaxPrice(event.target.value.replace(/\D/g, ""))} placeholder="不限" /></label>
      </div>
      <div className="picker-body">
        <div className="picker-results" aria-label="配件搜索结果">
          <div className="picker-result-meta"><strong>{filtered.length}</strong> 个候选</div>
          {filtered.map((item) => <button key={item.id} type="button" className={`picker-result ${selected?.id === item.id ? "selected" : ""}`} onClick={() => setSelectedId(item.id)}>
            <span><strong>{item.name}</strong><small>{item.brand} · {item.power_w || 0}W</small></span>
            <b>¥{formatMoney(item.price)}</b>
          </button>)}
          {!filtered.length && <div className="picker-empty">没有符合条件的配件，请放宽筛选条件。</div>}
        </div>
        <div className="picker-detail">
          {selected ? <>
            <div className="part-detail-title"><div><span className="eyebrow">配件详情</span><h3>{selected.name}</h3><p>{selected.summary || "当前为结构化参考数据，缺失字段会标记为待确认。"}</p></div><strong>¥{formatMoney(selected.price)}</strong></div>
            <div className="insight-metrics">
              <div><span>参考排名</span><strong>{selected.rank ? `#${selected.rank}` : "待确认"}</strong></div>
              <div><span>参考跑分</span><strong>{selected.benchmark_score ? formatMoney(selected.benchmark_score) : "待确认"}</strong></div>
              <div><span>参考百分位</span><strong>{selected.percentile !== null && selected.percentile !== undefined ? `${selected.percentile.toFixed(2)}%` : "待确认"}</strong></div>
            </div>
            <div className="spec-chip-grid">{Object.entries(selected.specs).slice(0, 14).map(([key, value]) => <div key={key}><span>{SPEC_LABELS[key] ?? key}</span><strong>{formatSpec(key, value)}</strong></div>)}</div>
            <section className="ai-review" aria-label="辅助点评"><div className="review-title"><BarChart3 size={17} /><strong>辅助点评</strong></div>
              {(selected.advantages ?? []).map((text) => <div className="review-line advantage" key={text}><CheckCircle2 size={16} /><span>{text}</span></div>)}
              {(selected.cautions ?? []).map((text) => <div className="review-line caution" key={text}><AlertTriangle size={16} /><span>{text}</span></div>)}
              {!(selected.advantages?.length || selected.cautions?.length) && <div className="review-line caution"><AlertTriangle size={16} /><span>该配件暂缺结构化点评，使用后仍会执行兼容性硬规则检查。</span></div>}
            </section>
            <div className="source-line"><span>来源：{selected.source}{selected.data_updated_at ? ` · 更新 ${selected.data_updated_at}` : ""}</span>{selected.url ? <a href={selected.url} target="_blank" rel="noreferrer">查看规格来源<ExternalLink size={13} /></a> : null}</div>
          </> : <div className="picker-empty">请选择一个候选配件。</div>}
        </div>
      </div>
      <footer className="picker-actions"><span>使用后会重新计算总价、功耗与兼容性。</span><button className="gold-button" type="button" disabled={!selected || busy} onClick={() => selected && onUse(selected)}>{busy ? "正在应用…" : `使用此${SLOT_LABELS[slot]}`}</button></footer>
    </section>
  </div>;
}
