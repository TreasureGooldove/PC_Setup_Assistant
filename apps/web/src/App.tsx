import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Cpu,
  Download,
  Gauge,
  Lock,
  MessageSquare,
  RefreshCw,
  Send,
  Settings2,
  Sparkles,
  Thermometer,
  Unlock,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { api, streamJob } from "./api";
import type { BuildItem, BuildPlan, ConversationResponse, NeedProfile, Part, PartCategory } from "./types";

const DEFAULT_PROFILE: NeedProfile = {
  budget: 8000,
  use_case: "游戏与日常",
  resolution: "2K",
  refresh_rate: 165,
  cpu_brand: "any",
  gpu_brand: "any",
  cooling: "any",
  aesthetics: "简洁",
  noise: "均衡",
  upgrade: "保留升级空间",
  existing_parts: [],
};

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

const DEMO_PARTS: Record<string, Part> = {
  cpu: { id: "demo-cpu", category: "cpu", name: "Ryzen 7 7700", brand: "AMD", price: 1599, source: "Fixture参考价", specs: { socket: "AM5", tdp: 65 }, power_w: 65 },
  motherboard: { id: "demo-board", category: "motherboard", name: "B650M WiFi 主板", brand: "AMD平台", price: 899, source: "Fixture参考价", specs: { socket: "AM5", memory_type: "DDR5" }, power_w: 0 },
  gpu: { id: "demo-gpu", category: "gpu", name: "GeForce RTX 4070 SUPER 12G", brand: "NVIDIA", price: 4499, source: "Fixture参考价", specs: { length_mm: 300 }, power_w: 220 },
  memory: { id: "demo-memory", category: "memory", name: "DDR5 6000 32GB套装", brand: "金百达", price: 699, source: "Fixture参考价", specs: { memory_type: "DDR5" }, power_w: 0 },
  storage: { id: "demo-storage", category: "storage", name: "1TB PCIe 4.0 固态硬盘", brand: "西数", price: 499, source: "Fixture参考价", specs: { capacity_gb: 1024 }, power_w: 0 },
  psu: { id: "demo-psu", category: "psu", name: "750W 金牌全模组电源", brand: "安钛克", price: 799, source: "Fixture参考价", specs: { wattage: 750 }, power_w: 0 },
  cooling: { id: "demo-cooling", category: "cooling", name: "双塔风冷散热器", brand: "利民", price: 199, source: "Fixture参考价", specs: { type: "air", capacity_w: 220 }, power_w: 0 },
  case: { id: "demo-case", category: "case", name: "通风型 ATX 机箱", brand: "乔思伯", price: 499, source: "Fixture参考价", specs: { gpu_length_mm: 360, cooler_height_mm: 170 }, power_w: 0 },
};

function demoPlans(profile: NeedProfile): BuildPlan[] {
  const now = new Date().toISOString();
  const styles: BuildPlan["style"][] = ["value", "balanced", "performance"];
  const titles = ["省心省预算", "均衡耐用", "高性能释放"];
  const summaries = ["优先把预算留给实际体验，适合主流游戏与日常使用。", "在性能、噪声和升级空间之间保持平衡。", "优先保障高刷新率和更长的使用周期。"];
  return styles.map((style, index) => {
    const items: BuildItem[] = Object.values(DEMO_PARTS).map((part) => ({ slot: part.category, part, locked: false, reason: `${part.category === "gpu" ? profile.resolution : "预算与兼容性"} 取向。` }));
    const multiplier = [0.78, 1, 1.12][index];
    if (index === 0) items.find((item) => item.slot === "gpu")!.part = { ...DEMO_PARTS.gpu, name: "Radeon RX 7600 8G", brand: "AMD", price: 2099, id: "demo-gpu-value", power_w: 165 };
    if (index === 2) items.find((item) => item.slot === "memory")!.part = { ...DEMO_PARTS.memory, name: "DDR5 6000 64GB套装", price: 1199, id: "demo-memory-performance" };
    const total = Math.round(items.reduce((sum, item) => sum + item.part.price, 0) * multiplier);
    return { id: `demo-${style}`, style, title: titles[index], summary: summaries[index], budget: profile.budget, total_price: total, estimated_power_w: 365 + index * 70, performance_score: 78 + index * 10, items, compatibility: [], created_at: now };
  });
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 0 }).format(value);
}

function localInterpret(content: string, current: NeedProfile): NeedProfile {
  const budgetMatch = content.match(/(\d+(?:\.\d+)?)\s*(万|w|W|元|块)?/);
  const next = { ...current };
  if (budgetMatch) next.budget = Math.max(2500, Math.min(100000, Math.round(Number(budgetMatch[1]) * (["万", "w", "W"].includes(budgetMatch[2] ?? "") ? 10000 : 1))));
  if (content.includes("水冷")) next.cooling = "water";
  if (content.includes("风冷")) next.cooling = "air";
  if (/N卡|英伟达|NVIDIA/i.test(content)) next.gpu_brand = "nvidia";
  if (/A卡|AMD显卡|镭/i.test(content)) next.gpu_brand = "amd";
  if (/AMD处理器|锐龙/i.test(content)) next.cpu_brand = "amd";
  if (/Intel|英特尔/i.test(content)) next.cpu_brand = "intel";
  if (content.includes("4K")) next.resolution = "4K";
  if (content.includes("1080")) next.resolution = "1080P";
  if (/剪辑|渲染|生产力/.test(content)) next.use_case = "视频剪辑与生产力";
  return next;
}

function localConversation(profile: NeedProfile): ConversationResponse {
  return { id: `local-${Date.now()}`, profile, messages: [{ role: "assistant", content: "你好，我会先了解你的用途和预算，再给出几套可解释的装机方案。", created_at: new Date().toISOString() }] };
}

export default function App() {
  const [profile, setProfile] = useState<NeedProfile>(DEFAULT_PROFILE);
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [plans, setPlans] = useState<BuildPlan[]>(() => demoPlans(DEFAULT_PROFILE));
  const [activePlanId, setActivePlanId] = useState("demo-balanced");
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("演示模式已就绪；启动 API 和 Worker 后可刷新真实任务与导出。");
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobMessage, setJobMessage] = useState("准备中");
  const [demoMode, setDemoMode] = useState(true);
  const stopStream = useRef<(() => void) | null>(null);

  useEffect(() => {
    let active = true;
    api.createConversation(DEFAULT_PROFILE).then((result) => {
      if (active) {
        setConversation(result);
        setProfile(result.profile);
        setDemoMode(false);
        setNotice("已连接到本地 API");
      }
    }).catch(() => {
      if (active) setConversation(localConversation(DEFAULT_PROFILE));
    });
    return () => { active = false; stopStream.current?.(); };
  }, []);

  const activePlan = useMemo(() => plans.find((plan) => plan.id === activePlanId) ?? plans[1], [activePlanId, plans]);
  const errors = activePlan?.compatibility.filter((item) => item.severity === "error") ?? [];
  const warnings = activePlan?.compatibility.filter((item) => item.severity === "warning") ?? [];

  const updateProfile = <K extends keyof NeedProfile>(key: K, value: NeedProfile[K]) => setProfile((current) => ({ ...current, [key]: value }));

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    const content = message.trim();
    if (!content) return;
    setMessage("");
    if (conversation && !demoMode) {
      try {
        setConversation(await api.sendMessage(conversation.id, content));
        setProfile((current) => localInterpret(content, current));
        setNotice("需求已更新");
        return;
      } catch { setNotice("API 暂不可用，已切换本地演示"); }
    }
    const next = localInterpret(content, profile);
    setProfile(next);
    setConversation((current) => ({ ...(current ?? localConversation(profile)), profile: next, messages: [...(current?.messages ?? []), { role: "user", content, created_at: new Date().toISOString() }, { role: "assistant", content: `收到：预算约 ${formatMoney(next.budget)} 元，目标 ${next.resolution}。可以点击生成方案。`, created_at: new Date().toISOString() }] }));
    setNotice("需求已更新（本地演示）");
  }

  async function handleGenerate() {
    setIsGenerating(true);
    setJobProgress(12);
    setJobMessage("读取需求");
    try {
      if (!demoMode && conversation) {
        await api.updateProfile(conversation.id, profile);
        const job = await api.generate(conversation.id);
        stopStream.current = streamJob(job.id, (event) => { setJobProgress(event.progress); setJobMessage(event.message); }, () => undefined);
        for (let attempt = 0; attempt < 40; attempt += 1) {
          const current = await api.getJob(job.id);
          setJobProgress(current.progress);
          setJobMessage(current.message);
          if (current.status === "completed") {
            const nextPlans = current.result?.plans ?? (await api.getPlans(conversation.id)).plans;
            setPlans(nextPlans);
            setActivePlanId(nextPlans[1]?.id ?? nextPlans[0]?.id ?? activePlanId);
            setNotice("三套方案已生成");
            return;
          }
          if (["dead_letter", "cancelled"].includes(current.status)) throw new Error(current.error ?? "任务未完成");
          await new Promise((resolve) => window.setTimeout(resolve, 500));
        }
        throw new Error("任务等待超时，请确认 Worker 已启动");
      }
      await new Promise((resolve) => window.setTimeout(resolve, 650));
      setJobProgress(100);
      setJobMessage("已完成");
      setPlans(demoPlans(profile));
      setActivePlanId("demo-balanced");
      setNotice("三套方案已生成（本地演示）");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "生成失败，请稍后重试");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleSwap(item: BuildItem) {
    try {
      if (!demoMode) {
        const catalog = await api.getCatalog(item.slot);
        const replacement = catalog.items.find((part) => part.id !== item.part.id);
        if (replacement && activePlan) {
          const updated = await api.replaceItem(activePlan.id, item.slot, replacement.id, item.locked);
          setPlans((current) => current.map((plan) => plan.id === updated.id ? updated : plan));
          return;
        }
      }
      setPlans((current) => current.map((plan) => plan.id === activePlan.id ? { ...plan, items: plan.items.map((entry) => entry.slot === item.slot ? { ...entry, part: { ...entry.part, name: `${entry.part.name} · 备选`, price: Math.max(99, entry.part.price - 100) } } : entry), total_price: Math.max(0, plan.total_price - 100) } : plan));
      setNotice(`${SLOT_LABELS[item.slot]}已替换为备选`);
    } catch { setNotice("替换失败，请稍后重试"); }
  }

  async function handleLock(item: BuildItem) {
    try {
      if (!demoMode && activePlan) await api.replaceItem(activePlan.id, item.slot, item.part.id, !item.locked);
    } catch { setNotice("锁定状态同步失败"); }
    setPlans((current) => current.map((plan) => plan.id === activePlan.id ? { ...plan, items: plan.items.map((entry) => entry.slot === item.slot ? { ...entry, locked: !entry.locked } : entry) } : plan));
  }

  async function handleExport() {
    if (demoMode || !activePlan) {
      setNotice("演示模式不生成文件；启动 API 和 Worker 后可导出 Excel");
      return;
    }
    try {
      const job = await api.exportPlan(activePlan.id);
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const current = await api.getJob(job.id);
        if (current.status === "completed") {
          window.open(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/api/jobs/${job.id}/download`, "_blank");
          setNotice("Excel 清单已准备完成");
          return;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 500));
      }
      setNotice("导出等待超时，请确认 Worker 已启动");
    } catch { setNotice("导出失败，请稍后重试"); }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><Sparkles size={18} aria-hidden="true" /></div>
          <div><p className="eyebrow">PC SETUP ASSISTANT</p><h1>智能装机搭子</h1></div>
        </div>
        <div className="topbar-actions">
          <span className={`connection-pill ${demoMode ? "is-demo" : ""}`}><span className="status-dot" />{demoMode ? "本地演示" : "API 已连接"}</span>
          <button className="icon-button" title="设置" aria-label="设置"><Settings2 size={19} /></button>
        </div>
      </header>

      <main className="workspace">
        <aside className="request-column panel">
          <div className="panel-heading"><div><p className="section-kicker">01 / 需求</p><h2>告诉我你想要什么</h2></div><MessageSquare size={20} aria-hidden="true" /></div>
          <p className="panel-intro">先给一个大概方向，细节可以边聊边调整。</p>
          <form className="needs-form" onSubmit={handleSend}>
            <label>预算范围<span className="field-value">¥{formatMoney(profile.budget)}</span><input aria-label="预算" type="range" min="2500" max="20000" step="500" value={profile.budget} onChange={(event) => updateProfile("budget", Number(event.target.value))} /><span className="range-caption"><span>¥2,500</span><span>¥20,000+</span></span></label>
            <label>主要用途<select value={profile.use_case} onChange={(event) => updateProfile("use_case", event.target.value)}><option>游戏与日常</option><option>视频剪辑与生产力</option><option>直播与创作</option><option>办公学习</option></select></label>
            <div className="field-grid"><label>目标分辨率<select value={profile.resolution} onChange={(event) => updateProfile("resolution", event.target.value)}><option>1080P</option><option>2K</option><option>4K</option></select></label><label>刷新率<select value={profile.refresh_rate} onChange={(event) => updateProfile("refresh_rate", Number(event.target.value))}><option value="60">60Hz</option><option value="144">144Hz</option><option value="165">165Hz</option><option value="240">240Hz</option></select></label></div>
            <fieldset><legend>品牌偏好</legend><div className="chip-grid"><button type="button" className={`choice-chip ${profile.cpu_brand === "amd" ? "selected" : ""}`} onClick={() => updateProfile("cpu_brand", profile.cpu_brand === "amd" ? "any" : "amd")}>AMD CPU</button><button type="button" className={`choice-chip ${profile.cpu_brand === "intel" ? "selected" : ""}`} onClick={() => updateProfile("cpu_brand", profile.cpu_brand === "intel" ? "any" : "intel")}>Intel CPU</button><button type="button" className={`choice-chip ${profile.gpu_brand === "nvidia" ? "selected" : ""}`} onClick={() => updateProfile("gpu_brand", profile.gpu_brand === "nvidia" ? "any" : "nvidia")}>NVIDIA 显卡</button><button type="button" className={`choice-chip ${profile.gpu_brand === "amd" ? "selected" : ""}`} onClick={() => updateProfile("gpu_brand", profile.gpu_brand === "amd" ? "any" : "amd")}>AMD 显卡</button></div></fieldset>
            <fieldset><legend>散热方式</legend><div className="cooling-choice"><button type="button" className={`cooling-option ${profile.cooling === "air" ? "selected" : ""}`} onClick={() => updateProfile("cooling", "air")}><Thermometer size={17} />风冷<span>安静、简单、好维护</span></button><button type="button" className={`cooling-option ${profile.cooling === "water" ? "selected" : ""}`} onClick={() => updateProfile("cooling", "water")}><RefreshCw size={17} />水冷<span>高性能、视觉更完整</span></button></div></fieldset>
            <button className="primary-button full-width" type="button" onClick={handleGenerate} disabled={isGenerating}>{isGenerating ? <><RefreshCw size={17} className="spin" />{jobMessage} {jobProgress}%</> : <><Sparkles size={17} />生成我的方案<ChevronRight size={17} /></>}</button>
          </form>
        </aside>

        <section className="conversation-column panel">
          <div className="panel-heading"><div><p className="section-kicker">02 / 对话</p><h2>一起把需求说清楚</h2></div><span className="step-count">{conversation?.messages.length ?? 1} 条记录</span></div>
          <div className="conversation-body" aria-live="polite">{(conversation?.messages ?? localConversation(profile).messages).map((entry, index) => <div className={`message-row ${entry.role}`} key={`${entry.created_at}-${index}`}><div className="avatar">{entry.role === "assistant" ? <Sparkles size={15} /> : "你"}</div><div className="message-bubble">{entry.content}</div></div>)}<div className="suggestion-line"><span>你也可以直接说：</span><button type="button" onClick={() => setMessage("预算 8000，想要 2K 游戏，N卡，风冷")}>预算和用途</button><button type="button" onClick={() => setMessage("我比较在意安静和后续升级")}>安静与升级</button></div></div>
          <form className="composer" onSubmit={handleSend}><input aria-label="输入你的装机需求" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="例如：8000 元，主要玩 2K 游戏，希望安静一些" /><button className="send-button" aria-label="发送需求" type="submit"><Send size={18} /></button></form>
        </section>

        <section className="plans-column panel">
          <div className="panel-heading"><div><p className="section-kicker">03 / 方案预览</p><h2>找到适合你的那一套</h2></div><Gauge size={20} aria-hidden="true" /></div>
          <div className="plan-tabs" role="tablist" aria-label="方案类型">{plans.map((plan) => <button key={plan.id} role="tab" aria-selected={plan.id === activePlanId} className={`plan-tab ${plan.id === activePlanId ? "active" : ""}`} onClick={() => setActivePlanId(plan.id)}><span>{plan.title}</span><small>{plan.style === "value" ? "轻预算" : plan.style === "balanced" ? "推荐" : "高性能"}</small></button>)}</div>
          {activePlan && <div className="plan-detail">
            <div className="plan-title-row"><div><h3>{activePlan.title}</h3><p>{activePlan.summary}</p></div><button className="secondary-button" type="button" onClick={handleExport}><Download size={16} />导出清单</button></div>
            <div className="metrics-grid"><div className="metric"><CircleDollarSign size={18} /><span>参考总价</span><strong>¥{formatMoney(activePlan.total_price)}</strong></div><div className="metric"><Gauge size={18} /><span>性能参考</span><strong>{activePlan.performance_score}<em>/ 100</em></strong></div><div className="metric"><Zap size={18} /><span>预计功耗</span><strong>{activePlan.estimated_power_w}<em>W</em></strong></div></div>
            <div className={`compatibility-banner ${errors.length ? "has-error" : warnings.length ? "has-warning" : "is-ok"}`}><div className="compat-icon">{errors.length ? <AlertTriangle size={18} /> : warnings.length ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}</div><div><strong>{errors.length ? `${errors.length} 项需要调整` : warnings.length ? `${warnings.length} 项建议关注` : "配置通过兼容性检查"}</strong><p>{errors[0]?.detail ?? warnings[0]?.detail ?? "插槽、尺寸、内存代际和电源余量均已检查。"}</p></div></div>
            <div className="parts-list">{activePlan.items.map((item) => <div className="part-row" key={item.slot}><div className={`part-icon ${item.slot}`}><Cpu size={17} /></div><div className="part-main"><span className="part-category">{SLOT_LABELS[item.slot]}</span><strong>{item.part.name}</strong><small>{item.part.brand} · {item.part.source}</small></div><div className="part-price">¥{formatMoney(item.part.price)}</div><button className="row-action" type="button" title={item.locked ? "解锁配置项" : "锁定配置项"} aria-label={`${item.locked ? "解锁" : "锁定"}${SLOT_LABELS[item.slot]}`} onClick={() => handleLock(item)}>{item.locked ? <Lock size={16} /> : <Unlock size={16} />}</button><button className="row-action swap" type="button" title="替换配置项" aria-label={`替换${SLOT_LABELS[item.slot]}`} onClick={() => handleSwap(item)}>换一件</button></div>)}</div>
            <div className="plan-footnote"><Check size={15} />所有价格为参考价，实际成交价以商品页面为准</div>
          </div>}
        </section>
      </main>
      <footer className="statusbar"><div><span className="status-dot" />{notice}</div><span className="footer-meta">数据仅供选购参考 · 兼容性由规则引擎复核</span></footer>
    </div>
  );
}
