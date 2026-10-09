import { useTranslation } from "react-i18next";

const KEYS = ["category_base_risk", "danger_words", "location_context", "duration", "repeat_reports", "policy_adjustment"];

/** Explains WHY a priority was given: the officer sees every contribution, not just a label. */
export default function Breakdown({ data }: { data: Record<string, unknown> }) {
  const { t } = useTranslation();
  const num = (k: string) => (typeof data[k] === "number" ? (data[k] as number) : 0);
  // new rows: points in "danger_words", the words themselves in "danger_words_found"; old rows had the list in "danger_words"
  const words = Array.isArray(data.danger_words_found) ? (data.danger_words_found as string[])
    : Array.isArray(data.danger_words) ? (data.danger_words as string[]) : [];
  const critical = typeof data.critical_reason === "string" ? data.critical_reason : null;
  const days = typeof data.duration_days === "number" ? data.duration_days : null;
  const note = typeof data.policy_note === "string" ? data.policy_note : null;
  const points = (k: string) => (k === "danger_words" && Array.isArray(data.danger_words) ? Math.min(25, 5 * words.length) : num(k));
  const evidence = Array.isArray(data.location_evidence) ? (data.location_evidence as string[]) : [];
  const rows = KEYS.map((k) => [k, points(k)] as [string, number]);
  const sum = rows.reduce((s, [, v]) => s + v, 0);
  return (
    <div className="text-sm">
      {critical && <p className="mb-2 rounded-lg bg-rose-100 px-3 py-2 font-semibold text-rose-900">{t("pred.critical")}: {critical}</p>}
      <table className="w-full">
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={k} className="border-b border-line last:border-0">
              <td className={`py-1.5 pr-2 ${v === 0 ? "text-slate-500" : "text-ink"}`}>
                {t(`bd.${k}`)}
                {k === "danger_words" && words.length > 0 && <span className="ml-1 text-xs text-ink-soft">({words.join(", ")})</span>}
                {k === "duration" && days !== null && <span className="ml-1 text-xs text-ink-soft">({days}d)</span>}
                {k === "policy_adjustment" && note && v !== 0 && <span className="ml-1 text-xs text-ink-soft">({note})</span>}
              </td>
              <td className={`py-1.5 text-right font-mono font-semibold ${v === 0 ? "text-slate-400" : v < 0 ? "text-rose-700" : "text-ink"}`}>{v > 0 ? "+" : ""}{v}</td>
            </tr>
          ))}
          <tr className="border-t-2 border-ink/20"><td className="py-1.5 font-bold">{t("pred.total")}</td><td className="py-1.5 text-right font-mono font-bold">{sum}</td></tr>
        </tbody>
      </table>
      {evidence.length > 0 && <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900"><b>{t("geo.evidenceTitle")}:</b> {evidence.join("; ")}</p>}
      <p className="hint">{t("pred.scoreHelp")}</p>
    </div>
  );
}
