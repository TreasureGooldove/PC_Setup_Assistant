import type { PartCategory } from "../../types";

export const SLOT_LABELS: Record<PartCategory, string> = {
  cpu: "处理器",
  motherboard: "主板",
  gpu: "显卡",
  memory: "内存",
  storage: "硬盘",
  psu: "电源",
  cooling: "散热",
  case: "机箱",
};

export const SPEC_LABELS: Record<string, string> = {
  brand_name: "品牌",
  model: "型号",
  product_name: "商品名称",
  socket: "适用 CPU 接口",
  chipset: "芯片组",
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
  vram_gb: "显存容量",
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
  max_memory: "最大内存",
  memory_slots: "内存插槽数量",
  m2_slots: "M.2 接口数量",
  sata_ports: "SATA 接口数量",
  gpu_slot: "显卡插槽",
  wifi: "无线连接",
  power_phase: "供电方案",
  rgb: "灯光同步",
  type: "散热方式",
  height_mm: "散热高度",
  radiator_mm: "冷排尺寸",
  capacity_w: "解热能力",
  supported_sockets: "支持平台",
  supported_form_factors: "支持板型",
  gpu_length_mm: "显卡限长",
  cooler_height_mm: "风冷限高",
};

export function formatMoney(value: number) {
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 }).format(
    value,
  );
}

export function formatSpec(key: string, value: unknown) {
  if (Array.isArray(value)) return value.join("、");
  if (typeof value === "boolean") return value ? "支持" : "不支持";
  if (value === null || value === undefined || value === "") return "待确认";
  if (typeof value === "number") {
    if (["tdp", "capacity_w", "wattage"].includes(key)) return `${value}W`;
    if (
      [
        "length_mm",
        "height_mm",
        "radiator_mm",
        "gpu_length_mm",
        "cooler_height_mm",
      ].includes(key)
    )
      return `${value}mm`;
    if (["capacity_gb", "max_memory_gb", "vram_gb"].includes(key))
      return `${value}GB`;
  }
  return String(value);
}
