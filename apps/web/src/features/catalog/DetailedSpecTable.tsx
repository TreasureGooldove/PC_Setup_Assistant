import type { PartCategory } from "../../types";
import {
  DETAIL_SPEC_GROUPS,
  formatSpec,
  getDetailedSpecRows,
  getDetailedSpecSummary,
} from "./partFormat";

interface DetailedSpecTableProps {
  category: PartCategory;
  specs: Record<string, unknown>;
  compact?: boolean;
}
export function DetailedSpecTable({
  category,
  specs,
  compact = false,
}: DetailedSpecTableProps) {
  const rows = getDetailedSpecRows(category, specs);
  const summary = getDetailedSpecSummary(category, specs);
  const groups = DETAIL_SPEC_GROUPS[category].map((group) => ({
    ...group,
    rows: rows.filter((row) => row.groupId === group.id),
  }));
  const extraRows = rows.filter((row) => row.groupId === "extra");

  return (
    <section
      className={`detailed-spec-table${compact ? " detailed-spec-table-compact" : ""}`}
      aria-label="完整配置参数"
    >
      <div className="detailed-spec-head">
        <div>
          <span className="eyebrow">完整配置参数</span>
          <h3>详细规格</h3>
        </div>
        <div className="detailed-spec-summary" aria-label="参数采集状态">
          <strong>{summary.available}</strong>
          <span>已采集</span>
          <i aria-hidden="true">·</i>
          <strong className="is-pending">{summary.pending}</strong>
          <span>待确认</span>
        </div>
      </div>
      <p className="detailed-spec-hint">
        已采集值来自结构化目录或商品页；未取得可靠来源的字段保留为“待确认”。
      </p>
      <div className="detailed-spec-groups">
        {groups.map((group) => (
          <section className="detailed-spec-group" key={group.id}>
            <h4>{group.label}</h4>
            <div className="detailed-spec-table-scroll">
              <table>
                <caption className="sr-only">{group.label}</caption>
                <thead>
                  <tr>
                    <th scope="col">参数</th>
                    <th scope="col">当前值</th>
                  </tr>
                </thead>
                <tbody>
                  {group.rows.map((row) => (
                    <tr key={row.key} className={row.available ? "" : "is-pending"}>
                      <th scope="row">{row.label}</th>
                      <td>{row.formatted}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
        {extraRows.length > 0 && (
          <section className="detailed-spec-group" key="extra">
            <h4>其他已采集字段</h4>
            <div className="detailed-spec-table-scroll">
              <table>
                <caption className="sr-only">其他已采集字段</caption>
                <thead>
                  <tr>
                    <th scope="col">参数</th>
                    <th scope="col">当前值</th>
                  </tr>
                </thead>
                <tbody>
                  {extraRows.map((row) => (
                    <tr key={row.key}>
                      <th scope="row">{row.label}</th>
                      <td>{formatSpec(row.key, row.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </section>
  );
}
