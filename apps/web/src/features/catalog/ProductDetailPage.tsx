import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  ExternalLink,
  RefreshCw,
  ShieldCheck,
  ShoppingBag,
} from "lucide-react";
import type { Part, ProductDetail } from "../../types";
import {
  formatMoney,
  formatSpec,
  SLOT_LABELS,
  SPEC_LABELS,
} from "./partFormat";

interface ProductDetailPageProps {
  detail: ProductDetail;
  busy?: boolean;
  onBack: () => void;
  onUse: (part: Part) => void | Promise<void>;
}

function statusLabel(status: string) {
  if (status === "live") return "实时读取";
  if (status === "reference") return "结构化参考";
  if (status === "fixture") return "示例数据";
  if (status === "disabled") return "未启用";
  if (status === "unconfigured") return "未配置";
  if (status === "unavailable") return "暂不可用";
  return status;
}

export function ProductDetailPage({
  detail,
  busy = false,
  onBack,
  onUse,
}: ProductDetailPageProps) {
  const { part } = detail;
  return (
    <main
      className="product-page page-view"
      aria-label={`${part.name} 商品详情`}
    >
      <button className="product-back" type="button" onClick={onBack}>
        <ArrowLeft size={17} />
        返回选配
      </button>
      <section className="product-hero glass-card">
        <div>
          <span className="eyebrow">
            {SLOT_LABELS[part.category]} / 商品详情
          </span>
          <h2>{part.name}</h2>
          <p>
            {part.summary ||
              "结构化参数会用于装机兼容性校验，缺失字段会明确标为待确认。"}
          </p>
          <div className="product-badges">
            <span>{part.brand}</span>
            <span>参考排名 {part.rank ? `#${part.rank}` : "待确认"}</span>
            <span>
              {part.data_updated_at
                ? `资料更新 ${part.data_updated_at}`
                : "更新时间待确认"}
            </span>
          </div>
        </div>
        <div className="product-primary-price">
          <span>目录参考价</span>
          <strong>¥{formatMoney(part.price)}</strong>
          <small>实际成交价以平台页面为准</small>
        </div>
      </section>

      <div className="product-layout">
        <div className="product-main-column">
          <section className="product-section glass-card">
            <div className="product-section-head">
              <div>
                <span className="eyebrow">平台比价</span>
                <h3>京东与拼多多</h3>
              </div>
              <span className="product-section-note">
                <Clock3 size={15} />
                报价带采集状态
              </span>
            </div>
            <div className="offer-grid">
              {detail.offers.map((offer) => (
                <article
                  className={`offer-card platform-${offer.platform}`}
                  key={`${offer.platform}-${offer.part_id}`}
                >
                  <div className="offer-head">
                    <strong>
                      {offer.platform === "jd"
                        ? "京东"
                        : offer.platform === "pdd"
                          ? "拼多多"
                          : offer.platform}
                    </strong>
                    <span className={offer.is_live ? "is-live" : "is-fixture"}>
                      {offer.is_live ? "实时" : "示例"}
                    </span>
                  </div>
                  <div className="offer-price">
                    <small>参考到手</small>
                    <strong>
                      ¥{formatMoney(offer.landed_price ?? offer.price)}
                    </strong>
                    {offer.list_price ? (
                      <del>¥{formatMoney(offer.list_price)}</del>
                    ) : null}
                  </div>
                  <p>{offer.seller || offer.source}</p>
                  <div className="offer-meta">
                    <span>{offer.status}</span>
                    <span>
                      {new Date(offer.captured_at).toLocaleString("zh-CN", {
                        hour12: false,
                      })}
                    </span>
                  </div>
                  {offer.url ? (
                    <a
                      className="offer-link"
                      href={offer.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      前往平台核价
                      <ExternalLink size={14} />
                    </a>
                  ) : null}
                </article>
              ))}
            </div>
          </section>

          <section className="product-section glass-card">
            <div className="product-section-head">
              <div>
                <span className="eyebrow">规格参数</span>
                <h3>逐项参数</h3>
              </div>
              <span className="product-section-note">
                <ShieldCheck size={15} />
                规则引擎会复核
              </span>
            </div>
            <div className="product-spec-grid">
              {Object.entries(part.specs).map(([key, value]) => (
                <div key={key}>
                  <span>{SPEC_LABELS[key] ?? key.replace(/^jd_/, "")}</span>
                  <strong>{formatSpec(key, value)}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="product-section glass-card">
            <div className="product-section-head">
              <div>
                <span className="eyebrow">选配提示</span>
                <h3>优势与注意事项</h3>
              </div>
            </div>
            <div className="product-review-grid">
              <div>
                {(part.advantages ?? []).map((text) => (
                  <p className="product-review good" key={text}>
                    <CheckCircle2 size={16} />
                    {text}
                  </p>
                ))}
              </div>
              <div>
                {(part.cautions ?? []).map((text) => (
                  <p className="product-review caution" key={text}>
                    <AlertTriangle size={16} />
                    {text}
                  </p>
                ))}
              </div>
            </div>
          </section>
        </div>

        <aside className="product-side-column">
          <section className="product-section glass-card">
            <span className="eyebrow">数据状态</span>
            <h3>这条数据从哪里来</h3>
            <div className="source-status-list">
              {detail.sources.map((source) => (
                <div
                  className={`source-status status-${source.status}`}
                  key={`${source.provider}-${source.kind}`}
                >
                  <div>
                    <strong>{source.provider}</strong>
                    <span>{source.kind === "price" ? "价格" : "参数"}</span>
                  </div>
                  <b>{statusLabel(source.status)}</b>
                  <p>{source.note}</p>
                </div>
              ))}
            </div>
          </section>
          <section className="product-section glass-card">
            <span className="eyebrow">参考信源</span>
            <h3>可人工核对</h3>
            <div className="evidence-list">
              {detail.evidence.map((evidence) => (
                <article key={`${evidence.source}-${evidence.title}`}>
                  <strong>{evidence.title}</strong>
                  <p>{evidence.summary}</p>
                  {evidence.url ? (
                    <a href={evidence.url} target="_blank" rel="noreferrer">
                      查看来源
                      <ExternalLink size={13} />
                    </a>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        </aside>
      </div>
      <div className="product-sticky-action">
        <div>
          <ShoppingBag size={18} />
          <span>当前选择</span>
          <strong>{part.name}</strong>
        </div>
        <button
          className="gold-button"
          type="button"
          disabled={busy}
          onClick={() => onUse(part)}
        >
          {busy ? (
            <>
              <RefreshCw className="spin" size={16} />
              正在应用…
            </>
          ) : (
            `使用此${SLOT_LABELS[part.category]}`
          )}
        </button>
      </div>
    </main>
  );
}
