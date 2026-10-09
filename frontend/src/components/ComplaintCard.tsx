import { AlertTriangle, Bot, Building2, ChevronDown, ChevronUp, MapPin, Siren, UserRound, UserCog } from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { Complaint } from "../types";
import { imageUrl } from "../api";
import { formatIST } from "../lib/time";
import { PriorityBadge, StatusBadge } from "./Badges";
import Breakdown from "./Breakdown";
import CategoryIcon from "./CategoryIcon";

const BAR: Record<string, string> = { low: "bg-emerald-500", medium: "bg-amber-400", high: "bg-orange-500", critical: "bg-rose-700" };

export default function ComplaintCard({ c, children, defaultOpen = false }: { c: Complaint; children?: ReactNode; defaultOpen?: boolean }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(defaultOpen);
  const modeLabel = c.route_mode === "auto" ? t("complaint.auto") : c.route_mode === "manual" ? t("complaint.manual") : t("complaint.reviewMode");
  const ModeIcon = c.route_mode === "auto" ? Bot : c.route_mode === "manual" ? UserCog : UserRound;
  return (
    <article className={`card relative overflow-hidden !p-0 ${c.urgent ? "ring-2 ring-rose-300" : ""}`}>
      <span className={`absolute inset-y-0 left-0 w-1.5 ${BAR[c.priority_level] ?? "bg-slate-300"}`} aria-hidden />
      <div className="p-5 pl-6 sm:p-6 sm:pl-7">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="font-mono text-sm font-semibold text-ink-soft">#{c.id}</span>
          {c.urgent && <span className="chip bg-rose-700 text-white"><Siren size={13} />{t("complaint.urgent")}</span>}
          <PriorityBadge level={c.priority_level} score={c.priority_score} />
          <StatusBadge status={c.status} />
          <time className="ml-auto text-sm text-ink-soft" dateTime={c.created_at}>{formatIST(c.created_at)}</time>
        </div>
        <p className="mb-4 whitespace-pre-wrap text-base leading-relaxed text-ink">{c.text}</p>
        <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-soft">
          <span className="inline-flex items-center gap-1.5"><CategoryIcon name={c.category} size={16} className="text-brand-700" />
            <b className="font-semibold text-ink">{t(`cat.${c.category}`, c.category)}</b>
            {c.secondary_category && <span>(+ {t(`cat.${c.secondary_category}`, c.secondary_category)}?)</span>}</span>
          <span className="inline-flex items-center gap-1.5"><Building2 size={16} className="text-brand-700" />{c.department ?? "-"}</span>
          <span className="inline-flex items-center gap-1.5"><UserRound size={16} className="text-brand-700" />{c.assigned_officer ?? t("complaint.unassigned")}</span>
          <span>{t("pred.confidence")}: <b className="text-ink">{Math.round(c.confidence * 100)}%</b></span>
        </div>
        <button className="mt-4 inline-flex cursor-pointer items-center gap-1 text-sm font-semibold text-brand-700 hover:underline" onClick={() => setOpen(!open)} aria-expanded={open}>
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}{open ? t("pred.hide") : t("pred.details")}
        </button>
        {open && (
          <div className="mt-4 grid gap-6 border-t border-line pt-4 md:grid-cols-2">
            <div>
              <h4 className="mb-2 text-base">{t("pred.breakdown")}</h4>
              <Breakdown data={c.priority_breakdown} />
            </div>
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="mb-1 text-base">{t("complaint.route")}</h4>
                <p className="inline-flex items-center gap-1.5 font-medium"><ModeIcon size={16} className="text-brand-700" />{modeLabel}</p>
                {c.route_reason && <p className="mt-1 text-ink-soft">{c.route_reason}</p>}
              </div>
              {c.location_flag && (
                <p role="status" className="flex items-start gap-1.5 rounded-lg bg-amber-50 px-3 py-2 font-medium text-amber-900"><AlertTriangle size={16} className="mt-0.5 shrink-0" />{t(`geo.flag.${c.location_flag}`)}</p>
              )}
              {c.geo_address && <p className="inline-flex items-start gap-1.5 text-ink-soft"><MapPin size={16} className="mt-0.5 shrink-0 text-brand-700" /><span><b className="text-ink">{t("geo.mapSays")}:</b> {c.geo_address}</span></p>}
              {c.address && <p className="inline-flex items-start gap-1.5 text-ink-soft"><MapPin size={16} className="mt-0.5 shrink-0 text-brand-700" />{c.address}{c.ward ? ` · ${c.ward}` : ""}</p>}
              {c.image_path && (
                <a href={imageUrl(c.image_path)} target="_blank" rel="noreferrer">
                  <img src={imageUrl(c.image_path)} alt={t("complaint.photo")} className="max-h-44 rounded-xl border border-line object-cover" />
                </a>
              )}
              {c.history && c.history.length > 0 && (
                <div>
                  <h4 className="mb-2 text-base">{t("complaint.history")}</h4>
                  <ol className="space-y-3 border-l-2 border-brand-200 pl-4">
                    {c.history.map((h, i) => (
                      <li key={i} className="relative">
                        <span className="absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full bg-brand-600" aria-hidden />
                        <StatusBadge status={h.new_status} />
                        <span className="ml-2 text-ink-soft">{formatIST(h.created_at)}</span>
                        {h.note && <p className="mt-1 text-ink">{h.note}</p>}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        )}
        {children && <div className="mt-4 border-t border-line pt-4 empty:hidden">{children}</div>}
      </div>
    </article>
  );
}
