import { Bot, CheckCheck, FolderOpen, Gauge, ListOrdered, Percent, Siren, Star, Target, Timer, type LucideProps } from "lucide-react";
import { useEffect, useState, type ComponentType } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import type { Analytics } from "../types";
import { ErrorBox, Spinner } from "../components/Badges";
import MapView from "../components/MapView";
import { shortDayIST } from "../lib/time";

const PRIO_COLOR: Record<string, string> = { critical: "bg-rose-700", high: "bg-orange-500", medium: "bg-amber-400", low: "bg-emerald-500" };

function Bars({ title, data, label, colors }: { title: string; data: Record<string, number>; label: (k: string) => string; colors?: Record<string, string> }) {
  const { t } = useTranslation();
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <section className="card">
      <h3 className="mb-4 text-lg">{title}</h3>
      {entries.length === 0 && <p className="text-sm text-ink-soft">{t("admin.noData")}</p>}
      <ul className="space-y-2.5">
        {entries.map(([k, v]) => (
          <li key={k} className="flex items-center gap-3 text-sm">
            <span className="w-32 shrink-0 truncate font-medium" title={label(k)}>{label(k)}</span>
            <div className="h-3 flex-1 rounded-full bg-slate-100"><div className={`h-3 rounded-full ${colors?.[k] ?? "bg-brand-600"}`} style={{ width: `${(v / max) * 100}%` }} /></div>
            <span className="w-8 text-right font-mono font-semibold">{v}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Tile({ Icon, label, value, help }: { Icon: ComponentType<LucideProps>; label: string; value: string | number; help?: string }) {
  return (
    <div className="card !p-4" title={help}>
      <div className="flex items-center gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-100 text-brand-800"><Icon size={20} /></span>
        <p className="text-sm font-medium leading-snug text-ink-soft">{label}</p>
      </div>
      <p className="mt-3 font-display text-3xl font-extrabold text-ink">{value}</p>
    </div>
  );
}

function fmtHours(h: number | null): string {
  if (h === null) return "-";
  if (h < 1) return `${Math.max(1, Math.round(h * 60))} min`;
  if (h < 48) return `${h.toFixed(1)} h`;
  return `${(h / 24).toFixed(1)} d`;
}

export default function AdminAnalytics() {
  const { t } = useTranslation();
  const [a, setA] = useState<Analytics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api<Analytics>("/admin/analytics").then(setA).catch((e) => setError((e as Error).message)); }, []);
  if (!a) return <div className="section py-8">{error ? <ErrorBox message={error} /> : <Spinner label={t("common.loading")} />}</div>;
  const pct = (x: number) => `${Math.round(x * 100)}%`;
  const maxDay = Math.max(1, ...a.per_day.map((d) => d.count));
  return (
    <div className="section space-y-6 py-8 lg:py-10">
      <header><h1 className="text-3xl sm:text-4xl">{t("admin.analyticsTitle")}</h1><p className="mt-2 text-ink-soft">{t("admin.analyticsSub")}</p></header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Tile Icon={ListOrdered} label={t("admin.total")} value={a.total} />
        <Tile Icon={FolderOpen} label={t("admin.open")} value={a.open} />
        <Tile Icon={CheckCheck} label={t("admin.resolutionRate")} value={pct(a.resolution_rate)} />
        <Tile Icon={Timer} label={t("admin.avgTime")} value={fmtHours(a.avg_resolution_hours)} />
        <Tile Icon={Bot} label={t("admin.autoRate")} value={pct(a.auto_route_rate)} help={t("admin.autoHelp")} />
        <Tile Icon={Gauge} label={t("admin.avgConf")} value={pct(a.avg_confidence)} />
        <Tile Icon={Siren} label={t("admin.urgent")} value={a.urgent_open} />
        <Tile Icon={Star} label={t("admin.avgRating")} value={a.avg_rating === null ? "-" : `${a.avg_rating} / 5`} />
      </div>

      <section className="card">
        <h3 className="mb-5 text-lg">{t("admin.perDay")}</h3>
        <div className="flex h-44 items-end gap-1.5 sm:gap-2" role="img" aria-label={t("admin.perDay")}>
          {a.per_day.map((d) => (
            <div key={d.date} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
              <span className="text-xs font-semibold text-ink">{d.count || ""}</span>
              <div className="w-full rounded-t-md bg-brand-600" style={{ height: `${(d.count / maxDay) * 100}%`, minHeight: d.count ? 4 : 2, opacity: d.count ? 1 : 0.25 }} />
            </div>
          ))}
        </div>
        <div className="mt-2 flex gap-1.5 sm:gap-2">
          {a.per_day.map((d, i) => <span key={d.date} className="flex-1 text-center text-[10px] leading-tight text-ink-soft sm:text-xs">{i % 2 === 0 || i === a.per_day.length - 1 ? shortDayIST(d.date) : ""}</span>)}
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <Bars title={t("admin.byCategory")} data={a.by_category} label={(k) => t(`cat.${k}`, k)} />
        <Bars title={t("admin.byPriority")} data={a.by_priority} label={(k) => t(`prio.${k}`, k)} colors={PRIO_COLOR} />
        <Bars title={t("admin.byStatus")} data={a.by_status} label={(k) => t(`status.${k}`, k)} />
        <Bars title={t("admin.byDepartment")} data={a.by_department} label={(k) => k} />
      </div>

      <section className="card">
        <h3 className="mb-1 text-lg">{t("admin.decisions")}: {a.admin_decisions} · {t("admin.changed")}: {a.admin_changed_prediction}</h3>
        <p className="mb-5 flex items-center gap-2 text-sm text-ink-soft"><Target size={16} />{t("admin.changedHelp")}</p>
        <h3 className="mb-3 flex items-center gap-2 text-lg"><Percent size={0} className="hidden" />{t("admin.hotspots")}</h3>
        {a.hotspots.length === 0 ? <p className="text-sm text-ink-soft">{t("admin.noHotspots")}</p> :
          <MapView height={340} markers={a.hotspots.map((h) => ({ lat: h.lat, lng: h.lng, label: `${h.count}`, radius: 6 + Math.min(20, h.count * 3) }))} />}
      </section>
    </div>
  );
}
