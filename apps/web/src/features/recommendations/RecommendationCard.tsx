import {
  AlertTriangle,
  CircleDollarSign,
  ExternalLink,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { BuildPlan, NeedProfile, Recommendation } from "../../types";

interface RecommendationCardProps {
  recommendation: Recommendation | null;
  plan: BuildPlan | undefined;
  profile: NeedProfile;
  loading: boolean;
  error: string;
  progress: number;
  message: string;
  onGenerate: () => void;
  onRegenerate: () => void;
  onOpenGame: () => void;
}

function providerLabel(provider: string) {
  if (provider === "qwen") return "Qwen 结构化建议";
  if (provider === "mock-fallback") return "本地降级建议";
  return "本地演示建议";
}

function priceStatusLabel(status: Recommendation["price_summary"]["status"]) {
  if (status === "within_budget") return "在预算内";
  if (status === "over_budget") return "超出预算";
  return "参考金额";
}

export function RecommendationCard({
  recommendation,
  plan,
  profile,
  loading,
  error,
  progress,
  message,
  onGenerate,
  onRegenerate,
  onOpenGame,
}: RecommendationCardProps) {
  if (loading) {
    return (
      <section
        className="recommendation-card recommendation-loading"
        aria-label="结构化装机建议"
        aria-live="polite"
      >
        <div className="recommendation-header">
          <div className="recommendation-title">
            <span className="recommendation-icon"><Sparkles size={17} /></span>
            <div>
              <span className="eyebrow">AI 辅助建议</span>
              <h5>正在整理这套配置</h5>
            </div>
          </div>
          <strong>{progress}%</strong>
        </div>
        <div
          className="recommendation-progress"
          role="progressbar"
          aria-label={`建议生成进度 ${progress}%`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
        >
          <span style={{ width: `${Math.max(0, Math.min(100, progress))}%` }} />
        </div>
        <p className="recommendation-status"><RefreshCw size={15} className="spin" />{message}</p>
        <p className="recommendation-caption">会先读取需求、价格状态与兼容性检查，再生成可核对的建议摘要。</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="recommendation-card recommendation-error" aria-label="结构化装机建议">
        <div className="recommendation-header">
          <div className="recommendation-title">
            <span className="recommendation-icon warning"><AlertTriangle size={17} /></span>
            <div>
              <span className="eyebrow">AI 辅助建议</span>
              <h5>建议暂时没有生成</h5>
            </div>
          </div>
        </div>
        <p>{error}</p>
        <button className="glass-button recommendation-action" type="button" onClick={onGenerate}>
          <RefreshCw size={16} />重试
        </button>
      </section>
    );
  }

  if (!recommendation || !plan) {
    return (
      <section className="recommendation-card recommendation-empty" aria-label="结构化装机建议">
        <div className="recommendation-header">
          <div className="recommendation-title">
            <span className="recommendation-icon"><Sparkles size={17} /></span>
            <div>
              <span className="eyebrow">AI 辅助建议</span>
              <h5>把依据讲清楚</h5>
            </div>
          </div>
        </div>
        <p>生成后可查看这套方案的需求理解、选型理由、兼容性结论和价格来源。</p>
        <button className="gold-button recommendation-action" type="button" onClick={onGenerate}>
          <Sparkles size={16} />生成结构化建议
        </button>
      </section>
    );
  }

  const compatibility = recommendation.compatibility_summary;
  const price = recommendation.price_summary;
  const gameEvidence = recommendation.evidence.some((item) => item.kind === "game");
  const compatibilityClass = compatibility.status === "error"
    ? "has-error"
    : compatibility.status === "warning"
      ? "has-warning"
      : "is-ok";

  return (
    <section className="recommendation-card" aria-label="结构化装机建议">
      <div className="recommendation-header">
        <div className="recommendation-title">
          <span className="recommendation-icon"><Sparkles size={17} /></span>
          <div>
            <span className="eyebrow">AI 辅助建议</span>
            <h5>{recommendation.headline}</h5>
          </div>
        </div>
        <div className="recommendation-meta">
          <span className="source-badge">{providerLabel(recommendation.provider)}</span>
          {recommendation.stale && <span className="stale-badge">方案已变化</span>}
        </div>
      </div>
      <p className="recommendation-summary">{recommendation.summary}</p>
      <div className="recommendation-profile">
        <ShieldCheck size={16} />
        <span>{recommendation.profile_summary}</span>
        <small>预算 ¥{profile.budget.toLocaleString("zh-CN")}</small>
      </div>

      <div className="recommendation-facts">
        <div className={`recommendation-fact ${compatibilityClass}`}>
          <div className="fact-label"><ShieldCheck size={16} />兼容性复核</div>
          <strong>{compatibility.passed_checks}/10 项通过</strong>
          <small>
            {compatibility.errors.length
              ? `${compatibility.errors.length} 项需调整`
              : compatibility.warnings.length
                ? `${compatibility.warnings.length} 项待确认`
                : "未发现硬性冲突"}
          </small>
        </div>
        <div className={`recommendation-fact price-${price.status}`}>
          <div className="fact-label"><CircleDollarSign size={16} />价格结论</div>
          <strong>¥{price.total_price.toLocaleString("zh-CN")}</strong>
          <small>{priceStatusLabel(price.status)}</small>
        </div>
      </div>

      <div className="recommendation-decisions">
        <div className="recommendation-subhead">为什么这样选</div>
        <ol>
          {recommendation.decisions.map((decision) => (
            <li key={decision.slot}>
              <div>
                <strong>{decision.part_name}</strong>
                <small>{decision.reason}</small>
              </div>
            </li>
          ))}
        </ol>
      </div>

      {(compatibility.errors.length > 0 || compatibility.warnings.length > 0) && (
        <div className={`recommendation-notices ${compatibility.errors.length ? "has-error" : "has-warning"}`}>
          <AlertTriangle size={16} />
          <div>
            {compatibility.errors.concat(compatibility.warnings).slice(0, 3).map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        </div>
      )}

      <details className="recommendation-evidence">
        <summary>查看依据与来源（{recommendation.evidence.length}）</summary>
        <div className="evidence-list">
          {recommendation.evidence.map((item) => (
            <div className="evidence-row" key={item.id}>
              <div>
                <strong>{item.label}</strong>
                <small>{item.source} · 可信度 {item.confidence === "high" ? "高" : item.confidence === "medium" ? "中" : "低"}</small>
                <p>{item.summary}</p>
              </div>
              {item.url && (
                <a href={item.url} target="_blank" rel="noreferrer" aria-label={`打开${item.label}来源`}>
                  <ExternalLink size={15} />
                </a>
              )}
            </div>
          ))}
          {price.source_notes.map((note) => <small className="price-note" key={note}>{note}</small>)}
        </div>
      </details>

      {(recommendation.uncertainties.length > 0 || recommendation.next_actions.length > 0) && (
        <div className="recommendation-next">
          {recommendation.uncertainties.length > 0 && (
            <div>
              <strong>还需确认</strong>
              <ul>{recommendation.uncertainties.map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          )}
          {recommendation.next_actions.length > 0 && (
            <div>
              <strong>下一步</strong>
              <ul>{recommendation.next_actions.map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          )}
        </div>
      )}

      <div className="recommendation-actions">
        {gameEvidence && (
          <button className="glass-button recommendation-action" type="button" onClick={onOpenGame}>
            查看游戏配置
          </button>
        )}
        <button className="glass-button recommendation-action" type="button" onClick={onRegenerate}>
          <RefreshCw size={15} />重新生成
        </button>
      </div>
      <p className="recommendation-caption">建议由结构化事实生成；金额、配件身份和兼容性以当前方案数据为准。</p>
    </section>
  );
}
