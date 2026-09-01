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
  series: "系列",
  manufacturer: "芯片厂商",
  chipset_vendor: "芯片厂商",
  gpu_chip: "显卡芯片",
  architecture: "架构",
  process: "制程工艺",
  launch_year: "上市年份",
  launch_date: "上市日期",
  socket: "适用 CPU 接口",
  chipset: "芯片组",
  tdp: "设计功耗",
  power_w: "整卡/参考功耗",
  score: "性能指数",
  cores_threads: "核心线程",
  physical_cores: "核心数",
  logical_threads: "线程数",
  base_clock: "基础频率",
  boost_clock: "加速频率",
  core_clock: "核心频率",
  memory_clock: "显存频率",
  max_turbo_power: "最大睿频功耗",
  integrated_graphics: "核显",
  l3_cache: "三级缓存",
  l2_cache: "二级缓存",
  memory_types: "内存支持",
  memory_channels: "内存通道",
  memory_description: "内存描述",
  cpu_type: "CPU 类型",
  chipset_description: "芯片组描述",
  max_memory_speed: "最高内存频率",
  pcie_version: "PCIe 版本",
  package: "封装形式",
  cooler_included: "盒装散热器",
  cuda_cores: "CUDA 核心",
  stream_processors: "流处理器",
  tensor_cores: "Tensor 核心",
  rt_cores: "光追核心",
  memory_bus: "显存位宽",
  memory_clock_mhz: "显存频率",
  length_mm: "长度",
  width_mm: "宽度",
  thickness_mm: "厚度",
  slot_count: "占用插槽",
  vram_gb: "显存容量",
  memory_bus_bit: "显存位宽",
  pcie_slot: "总线接口",
  power_connectors: "供电接口",
  outputs: "视频输出",
  hdmi: "HDMI 接口",
  displayport: "DisplayPort 接口",
  max_resolution: "最大分辨率",
  cooling: "散热设计",
  tgp: "整卡功耗",
  recommended_psu_w: "建议电源",
  memory_type: "内存代际",
  speed_mts: "内存速率",
  kit: "套装规格",
  module_count: "内存条数",
  timings: "时序",
  voltage: "工作电压",
  ecc: "ECC 校验",
  buffered: "是否缓冲",
  rank: "内存 Rank",
  xmp: "XMP",
  expo: "EXPO",
  heatspreader: "散热片",
  capacity_gb: "容量",
  interface: "接口标准",
  connector: "物理接口",
  protocol: "传输协议",
  storage_form_factor: "存储规格",
  controller: "主控",
  nand: "闪存类型",
  cache: "缓存",
  seq_read_mb_s: "顺序读取",
  seq_write_mb_s: "顺序写入",
  random_read_iops: "随机读取",
  random_write_iops: "随机写入",
  tbw: "写入寿命 TBW",
  warranty_years: "质保年限",
  heatsink: "散热装甲",
  wattage: "额定功率",
  rating: "认证等级",
  modular: "模组类型",
  atx_3_0: "ATX 3.0",
  atx_version: "ATX 版本",
  pcie_8pin_count: "PCIe 8Pin 数量",
  twelve_vhpwr: "12VHPWR / 12V-2x6",
  twelve_v_output: "12V 输出",
  efficiency: "转换效率",
  fan_size: "风扇尺寸",
  dimensions: "产品尺寸",
  form_factor: "板型/尺寸",
  max_memory_gb: "最大内存",
  max_memory: "最大内存",
  memory_slots: "内存插槽数量",
  pcie_slots: "PCIe 插槽",
  pcie_x16_slots: "PCIe x16 插槽",
  pcie_x1_slots: "PCIe x1 插槽",
  m2_slots: "M.2 接口数量",
  m2_interfaces: "M.2 通道",
  sata_ports: "SATA 接口数量",
  storage_interfaces: "存储接口",
  sata_speed: "SATA 速率",
  gpu_slot: "显卡插槽",
  usb_ports: "USB 接口",
  usb_c: "USB-C 接口",
  usb_header: "前置 USB 接针",
  other_interfaces: "其他接口",
  thunderbolt: "雷电扩展",
  onboard_video: "板载视频输出",
  wifi: "无线连接",
  wifi_version: "Wi-Fi 版本",
  bluetooth: "蓝牙",
  lan: "有线网卡",
  audio_codec: "音频芯片",
  power_phase: "供电方案",
  cpu_power_connector: "CPU 供电接口",
  motherboard_power_connector: "主板供电接口",
  fan_headers: "风扇接口",
  bios_flashback: "BIOS 刷新功能",
  rgb: "灯光同步",
  type: "散热方式",
  height_mm: "散热高度",
  radiator_mm: "冷排尺寸",
  radiator_size: "冷排规格",
  capacity_w: "解热能力",
  supported_sockets: "支持平台",
  fan_count: "风扇数量",
  fan_speed_rpm: "风扇转速",
  noise_db: "噪音",
  supported_form_factors: "支持板型",
  gpu_length_mm: "显卡限长",
  cooler_height_mm: "风冷限高",
  fan_support: "风扇位支持",
  front_io: "前置接口",
  psu_support: "电源兼容",
  drive_bays: "硬盘位",
  weight_kg: "重量",
};

export interface DetailedSpecField {
  key: string;
  label: string;
  aliases?: string[];
}

export interface DetailedSpecGroup {
  id: string;
  label: string;
  fields: DetailedSpecField[];
}

export interface DetailedSpecRow {
  groupId: string;
  groupLabel: string;
  key: string;
  label: string;
  value: unknown;
  formatted: string;
  available: boolean;
}

const field = (
  key: string,
  label: string,
  aliases?: string[],
): DetailedSpecField => ({ key, label, aliases });

const group = (
  id: string,
  label: string,
  fields: DetailedSpecField[],
): DetailedSpecGroup => ({ id, label, fields });

/**
 * 详情页字段清单。它是展示 schema，不是数据生成器；没有来源的值必须保持“待确认”。
 */
export const DETAIL_SPEC_GROUPS: Record<PartCategory, DetailedSpecGroup[]> = {
  cpu: [
    group("identity", "基础资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("series", "系列"),
      field("socket", "CPU 插槽"),
      field("architecture", "架构"),
      field("process", "制程工艺"),
      field("launch_year", "上市年份", ["launch_date"]),
      field("package", "封装形式"),
    ]),
    group("compute", "核心与频率", [
      field("cores_threads", "核心 / 线程", ["physical_cores", "logical_threads"]),
      field("base_clock", "基础频率"),
      field("boost_clock", "加速频率", ["core_clock"]),
      field("l2_cache", "二级缓存"),
      field("l3_cache", "三级缓存"),
      field("integrated_graphics", "核显"),
      field("tdp", "设计功耗"),
      field("max_turbo_power", "最大睿频功耗"),
      field("cooler_included", "盒装散热器"),
    ]),
    group("platform", "平台与内存", [
      field("memory_types", "支持内存", ["memory_type"]),
      field("memory_channels", "内存通道"),
      field("max_memory_gb", "最大内存"),
      field("max_memory_speed", "最高内存频率"),
      field("pcie_version", "PCIe 版本"),
      field("score", "性能指数"),
    ]),
  ],
  motherboard: [
    group("identity", "平台资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("socket", "CPU 插槽"),
      field("chipset", "芯片组"),
      field("chipset_description", "芯片组描述"),
      field("cpu_type", "CPU 类型"),
      field("form_factor", "板型"),
      field("memory_type", "内存代际"),
    ]),
    group("memory", "内存支持", [
      field("memory_slots", "内存插槽数量"),
      field("max_memory_gb", "最大内存", ["max_memory"]),
      field("max_memory_speed", "最高内存频率"),
      field("memory_channels", "内存通道"),
      field("memory_description", "内存描述"),
    ]),
    group("expansion", "扩展与存储", [
      field("gpu_slot", "主显卡插槽"),
      field("pcie_slots", "PCIe 插槽"),
      field("pcie_version", "PCIe 版本"),
      field("m2_slots", "M.2 接口数量"),
      field("m2_interfaces", "M.2 通道"),
      field("sata_ports", "SATA 接口数量"),
      field("sata_speed", "SATA 速率"),
      field("storage_interfaces", "存储接口"),
      field("usb_ports", "USB 接口"),
      field("usb_c", "USB-C 接口"),
      field("usb_header", "内置 USB 接针"),
      field("other_interfaces", "其他接口"),
      field("thunderbolt", "雷电扩展"),
    ]),
    group("network", "网络与功能", [
      field("lan", "有线网卡"),
      field("wifi", "无线连接"),
      field("wifi_version", "Wi-Fi 版本"),
      field("bluetooth", "蓝牙"),
      field("audio_codec", "音频芯片"),
      field("power_phase", "供电相数"),
      field("cpu_power_connector", "CPU 供电接口"),
      field("rgb", "灯光同步"),
      field("bios_flashback", "BIOS 刷新功能"),
    ]),
  ],
  gpu: [
    group("identity", "芯片资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("chipset_vendor", "芯片厂商"),
      field("gpu_chip", "显卡芯片", ["chipset"]),
      field("series", "显卡系列"),
      field("architecture", "架构"),
      field("launch_date", "上市日期", ["launch_year"]),
    ]),
    group("compute", "核心与显存", [
      field("cuda_cores", "CUDA 核心"),
      field("stream_processors", "流处理器"),
      field("tensor_cores", "Tensor 核心"),
      field("rt_cores", "光追核心"),
      field("core_clock", "核心频率", ["base_clock"]),
      field("boost_clock", "加速频率"),
      field("vram_gb", "显存容量"),
      field("memory_type", "显存类型"),
      field("memory_clock", "显存频率", ["memory_clock_mhz"]),
      field("memory_bus_bit", "显存位宽", ["memory_bus"]),
      field("score", "性能指数"),
    ]),
    group("io", "接口与尺寸", [
      field("pcie_slot", "PCIe 接口"),
      field("outputs", "视频输出"),
      field("hdmi", "HDMI 接口"),
      field("displayport", "DisplayPort 接口"),
      field("power_connectors", "供电接口"),
      field("length_mm", "长度"),
      field("width_mm", "宽度"),
      field("thickness_mm", "厚度"),
      field("slot_count", "占用插槽"),
      field("max_resolution", "最大分辨率"),
    ]),
    group("power", "功耗与散热", [
      field("power_w", "整卡/参考功耗"),
      field("tgp", "整卡功耗"),
      field("recommended_psu_w", "建议电源"),
      field("cooling", "散热设计"),
    ]),
  ],
  memory: [
    group("identity", "基础资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("memory_type", "内存代际"),
      field("capacity_gb", "容量"),
      field("kit", "套装规格"),
      field("module_count", "内存条数"),
    ]),
    group("performance", "频率与时序", [
      field("speed_mts", "频率"),
      field("timings", "时序"),
      field("voltage", "工作电压"),
      field("rank", "内存 Rank"),
      field("ecc", "ECC 校验"),
      field("buffered", "是否缓冲"),
    ]),
    group("features", "特性与外观", [
      field("xmp", "XMP"),
      field("expo", "EXPO"),
      field("heatspreader", "散热片"),
      field("rgb", "灯光同步"),
      field("warranty_years", "质保年限"),
    ]),
  ],
  storage: [
    group("identity", "基础资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("capacity_gb", "容量"),
      field("storage_form_factor", "存储规格", ["form_factor"]),
      field("interface", "接口标准"),
      field("connector", "物理接口"),
      field("protocol", "传输协议"),
    ]),
    group("hardware", "硬件构成", [
      field("controller", "主控"),
      field("nand", "闪存类型"),
      field("cache", "缓存"),
      field("heatsink", "散热装甲"),
    ]),
    group("performance", "性能与寿命", [
      field("seq_read_mb_s", "顺序读取"),
      field("seq_write_mb_s", "顺序写入"),
      field("random_read_iops", "随机读取"),
      field("random_write_iops", "随机写入"),
      field("tbw", "写入寿命 TBW"),
      field("warranty_years", "质保年限"),
    ]),
  ],
  psu: [
    group("identity", "基础资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("wattage", "额定功率"),
      field("rating", "认证等级"),
      field("modular", "模组类型"),
      field("dimensions", "产品尺寸"),
    ]),
    group("standard", "规范与输出", [
      field("atx_version", "ATX 版本", ["atx_3_0"]),
      field("twelve_v_output", "12V 输出"),
      field("efficiency", "转换效率"),
      field("pcie_8pin_count", "PCIe 8Pin 数量"),
      field("twelve_vhpwr", "12VHPWR / 12V-2x6"),
      field("pcie_connectors", "PCIe 接口"),
    ]),
    group("service", "散热与售后", [
      field("fan_size", "风扇尺寸"),
      field("fan_count", "风扇数量"),
      field("warranty_years", "质保年限"),
    ]),
  ],
  cooling: [
    group("identity", "基础资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("type", "散热方式"),
      field("supported_sockets", "支持平台"),
      field("capacity_w", "解热能力"),
    ]),
    group("size", "尺寸与安装", [
      field("height_mm", "散热高度"),
      field("radiator_mm", "冷排尺寸"),
      field("radiator_size", "冷排规格"),
      field("fan_size", "风扇尺寸"),
      field("fan_count", "风扇数量"),
      field("connector", "供电/控制接口"),
    ]),
    group("acoustics", "风扇与灯效", [
      field("fan_speed_rpm", "风扇转速"),
      field("noise_db", "噪音"),
      field("rgb", "灯光同步"),
    ]),
  ],
  case: [
    group("identity", "基础资料", [
      field("brand_name", "品牌", ["manufacturer"]),
      field("model", "型号", ["product_name"]),
      field("form_factor", "机箱定位"),
      field("supported_form_factors", "支持板型"),
      field("dimensions", "机箱尺寸"),
      field("weight_kg", "重量"),
    ]),
    group("clearance", "装机空间", [
      field("gpu_length_mm", "显卡限长"),
      field("cooler_height_mm", "风冷限高"),
      field("radiator_mm", "冷排支持"),
      field("psu_support", "电源兼容"),
    ]),
    group("expansion", "扩展与接口", [
      field("fan_support", "风扇位支持"),
      field("fan_count", "预装风扇数量"),
      field("front_io", "前置接口"),
      field("drive_bays", "硬盘位"),
      field("rgb", "灯光同步"),
    ]),
  ],
};

function hasSpecValue(value: unknown): boolean {
  return !(
    value === null ||
    value === undefined ||
    value === "" ||
    (Array.isArray(value) && value.length === 0)
  );
}

export function specLabel(key: string): string {
  if (SPEC_LABELS[key]) return SPEC_LABELS[key];
  if (key.startsWith("jd_")) return `商品页 · ${key.slice(3)}`;
  return key.replaceAll("_", " ");
}

export function getDetailedSpecRows(
  category: PartCategory,
  specs: Record<string, unknown>,
): DetailedSpecRow[] {
  const groups = DETAIL_SPEC_GROUPS[category];
  const knownKeys = new Set<string>();
  const knownLabels = new Set<string>();
  const rows = groups.flatMap((currentGroup) =>
    currentGroup.fields.map((definition) => {
      const candidateKeys = [definition.key, ...(definition.aliases ?? [])];
      candidateKeys.forEach((key) => knownKeys.add(key));
      knownLabels.add(definition.label);
      const sourceKey = candidateKeys.find((key) => hasSpecValue(specs[key]));
      const value = sourceKey ? specs[sourceKey] : undefined;
      return {
        groupId: currentGroup.id,
        groupLabel: currentGroup.label,
        key: definition.key,
        label: definition.label,
        value,
        formatted: formatSpec(sourceKey ?? definition.key, value),
        available: hasSpecValue(value),
      };
    }),
  );
  const extras = Object.entries(specs).filter(
    ([key, value]) =>
      key !== "catalog_kind" &&
      !knownKeys.has(key) &&
      !knownLabels.has(specLabel(key)) &&
      hasSpecValue(value),
  );
  if (extras.length) {
    rows.push(
      ...extras.map(([key, value]) => ({
        groupId: "extra",
        groupLabel: "其他已采集字段",
        key,
        label: specLabel(key),
        value,
        formatted: formatSpec(key, value),
        available: true,
      })),
    );
  }
  return rows;
}

export function getDetailedSpecSummary(
  category: PartCategory,
  specs: Record<string, unknown>,
) {
  const rows = getDetailedSpecRows(category, specs);
  return {
    total: rows.length,
    available: rows.filter((row) => row.available).length,
    pending: rows.filter((row) => !row.available).length,
  };
}

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
    if (["tdp", "capacity_w", "wattage", "power_w", "tgp", "recommended_psu_w", "max_turbo_power"].includes(key)) return `${value}W`;
    if (
      [
        "length_mm",
        "height_mm",
        "radiator_mm",
        "gpu_length_mm",
        "cooler_height_mm",
        "width_mm",
        "thickness_mm",
      ].includes(key)
      )
      return `${value}mm`;
    if (["capacity_gb", "max_memory_gb", "vram_gb"].includes(key))
      return `${value}GB`;
    if (key === "memory_bus_bit") return `${value}bit`;
    if (key === "speed_mts") return `${value}MT/s`;
    if (key === "fan_speed_rpm") return `${value}rpm`;
    if (["warranty_years", "launch_year"].includes(key)) return `${value}年`;
    if (["seq_read_mb_s", "seq_write_mb_s"].includes(key)) return `${value}MB/s`;
  }
  return String(value);
}
