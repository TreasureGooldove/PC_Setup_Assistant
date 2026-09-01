import { Clock3, ExternalLink } from "lucide-react";
import type { Offer } from "../../types";
import { formatMoney } from "./partFormat";

interface OfferComparisonProps {
  offers: Offer[];
  compact?: boolean;
  loading?: boolean;
}

function platformLabel(platform: Offer["platform"]) {
  if (platform === "jd") return "京东";
  if (platform === "pdd") return "拼多多";
  if (platform === "taobao") return "淘宝";
  return platform;
}

function captureLabel(value?: string | null) {
  if (!value) return "没有报价快照";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "采集时间待确认";
  return date.toLocaleString("zh-CN", { hour12: false });
}

function offerState(offer: Offer) {
  if (offer.is_live) return { label: "实时", className: "is-live" };
  if (offer.status === "公开参考价") {
    return { label: "公开参考", className: "is-reference" };
  }
  if (offer.price !== null && offer.price !== undefined) {
    return { label: "参考价", className: "is-reference" };
  }
  return { label: "待联网", className: "is-pending" };
}

function OfferCard({ offer }: { offer: Offer }) {
  const state = offerState(offer);
  const amount = offer.landed_price ?? offer.price;
  return (
    <article
      className={`offer-card platform-${offer.platform}`}
      data-testid={`offer-${offer.platform}`}
    >
      <div className="offer-head">
        <strong>{platformLabel(offer.platform)}</strong>
        <span className={state.className}>{state.label}</span>
      </div>
      <div className="offer-price">
        <small>
          {offer.is_live
            ? "实时到手"
            : amount === null || amount === undefined
              ? "当前未取得金额"
              : "页面参考价"}
        </small>
        <strong>
          {amount === null || amount === undefined
            ? "待联网"
            : `¥${formatMoney(amount)}`}
        </strong>
        {offer.list_price && amount !== null && amount !== undefined ? (
          <del>¥{formatMoney(offer.list_price)}</del>
        ) : null}
      </div>
      <p>{offer.seller || "店铺信息待取得"}</p>
      <p className="offer-source">来源：{offer.source}</p>
      {offer.coupon_note ? (
        <p className="offer-coupon">优惠：{offer.coupon_note}</p>
      ) : null}
      <div className="offer-meta">
        <span>{offer.status}</span>
        <span>{captureLabel(offer.captured_at)}</span>
      </div>
      {offer.url ? (
        <a
          className="offer-link"
          href={offer.url}
          target="_blank"
          rel="noreferrer"
        >
          前往平台核价
          <ExternalLink size={14} aria-hidden="true" />
        </a>
      ) : null}
    </article>
  );
}

export function OfferComparison({
  offers,
  compact = false,
  loading = false,
}: OfferComparisonProps) {
  const className = compact
    ? "picker-offer-comparison"
    : "product-section glass-card";

  return (
    <section className={className} aria-label="平台报价">
      <div className="product-section-head">
        <div>
          <span className="eyebrow">平台比价</span>
          <h3>{compact ? "京东与拼多多价格" : "京东与拼多多"}</h3>
        </div>
        <span className="product-section-note">
          <Clock3 size={15} aria-hidden="true" />
          报价带采集状态
        </span>
      </div>
      {loading ? (
        <div className="offer-loading" aria-live="polite">
          正在读取该型号的平台报价…
        </div>
      ) : offers.length ? (
        <div className="offer-grid">
          {offers.map((offer) => (
            <OfferCard
              key={`${offer.platform}-${offer.source}-${offer.part_id}`}
              offer={offer}
            />
          ))}
        </div>
      ) : (
        <div className="offer-loading" aria-live="polite">
          暂无可展示报价，请稍后重试或前往平台搜索。
        </div>
      )}
    </section>
  );
}
