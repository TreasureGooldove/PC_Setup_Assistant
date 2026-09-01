import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Circle,
  ExternalLink,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import type {
  AgentStage,
  BuildPlan,
  GameRequirement,
  NeedProfile,
  Recommendation,
} from "../../types";

interface RequestInsightPanelProps {
  profile: NeedProfile;
  gameRequirement: GameRequirement | null;
  recommendation: Recommendation | null;
  plan: BuildPlan | undefined;
  busy: boolean;
  planBusy: boolean;
  progress: number;
  message: string;
  error: string;
  onGenerate: () => void;
  onViewResult: () => void;
}

const FALLBACK_STAGES: AgentStage[] = [
  {
    id: "need",
    label: "需求识别",
    status: "waiting",
    summary: "等待你提交预算、用途和偏好。",
    sources: ["用户输入"],
  },
  {
    id: "research",
    label: "游戏与资料",
    status: "waiting",
    summary: "识别游戏后载入官方配置；社区资料会单独标记。",
    sources: ["官方资料", "社区参考"],
  },
  {
    id: "candidates",
    label: "候选与价格",
    status: "waiting",
    summary: "整理候选配件和当前价格状态。",
    sources: ["候选目录", "报价状态"],
  },
  {
    id: "compatibility",
    label: "兼容性复核",
    status: "waiting",
    summary: "按插槽、尺寸、接口和电源规则复核。",
    sources: ["确定性规则"],
  },
  {
    id: "result",
    label: "生成结论",
    status: "waiting",
    summary: "将事实整理为可核对的建议。",
    sources: ["结构化结果"],
  },
];

function stageIcon(stage: AgentStage) {
  if (stage.status === "completed") return <CheckCircle2 size={15} />;
  if (stage.status === "running") return <RefreshCw size={15} className="spin" />;
  if (stage.status === "failed") return <AlertTriangle size={15} />;
  return <Circle size={15} />;
}

function stageStatusLabel(status: AgentStage["status"]) {
  if (status === "completed") return "已完成";
  if (status === "running") return "进行中";
  if (status === "failed") return "失败";
  if (status === "waiting") return "待取得";
  return "待处理";
}

function buildLiveStages(
  profile: NeedProfile,
  gameRequirement: GameRequirement | null,
  busy: boolean,
  planBusy: boolean,
  progress: number,
  message: string,
): AgentStage[] {
  if (!busy && !planBusy && progress === 0) {
    return FALLBACK_STAGES.map((stage) =>
      stage.id === "need"
        ? {
            ...stage,
            status: "completed",
            summary: `已读取预算 ${profile.budget.toLocaleString("zh-CN")} 元和 ${profile.use_case} 用途。`,
          }
        : stage,
    );
  }
  const activeIndex = progress >= 85 ? 4 : progress >= 55 ? 3 : progress >= 35 ? 2 : 1;
  return FALLBACK_STAGES.map((stage, index) => {
    const status: AgentStage["status"] =
      index < activeIndex ? "completed" : index === activeIndex ? "running" : "pending";
    let summary = stage.summary;
    if (stage.id === "need") {
      summary = `已读取预算 ${profile.budget.toLocaleString("zh-CN")} 元和 ${profile.use_case} 用途。`;
    } else if (stage.id === "research" && gameRequirement) {
      summary = `已识别 ${gameRequirement.name}，正在核对 ${gameRequirement.source_kind === "official" ? "官方" : "游戏商店"}资料。`;
    } else if (index === activeIndex) {
      summary = message || stage.summary;
    }
    return { ...stage, status, summary };
  });
}

export function RequestInsightPanel({
  profile,
  gameRequirement,
  recommendation,
  plan,
  busy,
  planBusy,
  progress,
  message,
  error,
  onGenerate,
  onViewResult,
}: RequestInsightPanelProps) {
  const trace = recommendation?.agent_trace;
  const stages = trace?.stages ?? buildLiveStages(
    profile,
    gameRequirement,
    busy,
    planBusy,
    progress,
    message,
  );
  const displayProgress = recommendation ? 100 : Math.max(0, Math.min(100, progress));

  return (
    <section
      className="request-insight"
      aria-label="AI 工作摘要"
      aria-busy={busy || planBusy}
    >
      <div className="request-insight-head">
        <div className="request-insight-title">
          <span className="request-insight-icon"><Sparkles size={15} /></span>
          <div>
            <span className="eyebrow">AI 工作摘要</span>
            <strong>把依据整理给你看</strong>
          </div>
        </div>
        <span className="request-insight-mode">
          {trace?.mode === "live" ? "模型已参与" : trace?.mode === "fallback" ? "模型降级" : "本地可复现"}
        </span>
      </div>

      <p className="request-insight-caption">
        展示可核对的阶段、来源和结果摘要，不展示模型内部隐式推理或原始工具日志。
      </p>

      {(busy || planBusy || recommendation) && (
        <div
          className="request-insight-progress"
          role="progressbar"
          aria-label={`AI 工作摘要进度 ${displayProgress}%`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={displayProgress}
        >
          <span style={{ width: `${displayProgress}%` }} />
        </div>
      )}

      <div className="request-insight-stages" aria-live="polite">
        {stages.map((stage) => (
          <div className={`request-insight-stage ${stage.status}`} key={stage.id}>
            <span className="request-insight-stage-icon" aria-hidden="true">{stageIcon(stage)}</span>
            <div>
              <div className="request-insight-stage-head">
                <strong>{stage.label}</strong>
                <small>{stageStatusLabel(stage.status)}</small>
              </div>
              <p>{stage.summary}</p>
              <div className="request-insight-sources">
                {stage.sources.map((source) => <span key={source}>{source}</span>)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {recommendation ? (
        <div className="request-insight-result">
          <div className="request-insight-result-label">结构化结果</div>
          <strong>{recommendation.headline}</strong>
          <p>{recommendation.agent_trace.result_summary}</p>
          <div className="request-insight-result-meta">
            <span>{recommendation.provider === "qwen" ? "Qwen" : "本地建议"}</span>
            <span>{plan ? `当前方案 ¥${plan.total_price.toLocaleString("zh-CN")}` : "已生成方案"}</span>
          </div>
          <button className="request-insight-link" type="button" onClick={onViewResult}>
            查看完整建议与依据 <ChevronRight size={14} />
          </button>
        </div>
      ) : (
        <div className="request-insight-actions">
          <button
            className="request-insight-generate"
            type="button"
            onClick={onGenerate}
            disabled={busy || planBusy}
          >
            {busy || planBusy ? <RefreshCw size={15} className="spin" /> : <Sparkles size={15} />}
            {busy || planBusy ? (message || "正在整理") : "用当前参数生成"}
          </button>
          {gameRequirement && (
            <span className="request-insight-game">
              已识别：{gameRequirement.name}
              {gameRequirement.source_kind === "official" && " · 官方资料"}
            </span>
          )}
        </div>
      )}

      {error && (
        <div className="request-insight-error" role="alert">
          <AlertTriangle size={15} />
          <span>{error}</span>
          <button type="button" onClick={onGenerate}>重试</button>
        </div>
      )}

      {trace?.stages.some((stage) => stage.id === "research" && stage.sources.includes("百度贴吧社区搜索")) && (
        <p className="request-insight-footnote">
          社区帖子只作低可信度补充，购买和兼容性判断仍以官方资料、商品参数和规则检查为准。
          <ExternalLink size={12} aria-hidden="true" />
        </p>
      )}
    </section>
  );
}
