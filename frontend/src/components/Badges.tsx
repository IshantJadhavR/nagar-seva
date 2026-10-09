import { AlertTriangle, CheckCircle2, CircleDot, Clock3, Inbox, RotateCcw, ShieldCheck, UserCheck, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

const PRIO: Record<string, string> = {
  low: "bg-emerald-100 text-emerald-900",
  medium: "bg-amber-100 text-amber-900",
  high: "bg-orange-200 text-orange-950",
  critical: "bg-rose-700 text-white",
};
const STATUS: Record<string, [string, ReactNode]> = {
  in_review: ["bg-violet-100 text-violet-900", <Inbox key="i" size={13} />],
  assigned: ["bg-sky-100 text-sky-900", <UserCheck key="a" size={13} />],
  in_progress: ["bg-brand-100 text-brand-900", <Clock3 key="p" size={13} />],
  resolved: ["bg-teal-100 text-teal-900", <CheckCircle2 key="r" size={13} />],
  reopened: ["bg-rose-100 text-rose-900", <RotateCcw key="o" size={13} />],
  closed: ["bg-slate-200 text-slate-800", <ShieldCheck key="c" size={13} />],
  rejected: ["bg-zinc-200 text-zinc-800", <XCircle key="x" size={13} />],
};

export function PriorityBadge({ level, score }: { level: string; score?: number }) {
  const { t } = useTranslation();
  return (
    <span className={`chip ${PRIO[level] ?? "bg-slate-100 text-slate-800"}`}>
      {level === "critical" ? <AlertTriangle size={13} /> : <CircleDot size={13} />}
      {t(`prio.${level}`, level)}{score !== undefined ? ` · ${score}` : ""}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const [cls, icon] = STATUS[status] ?? ["bg-slate-100 text-slate-800", null];
  return <span className={`chip ${cls}`}>{icon}{t(`status.${status}`, status)}</span>;
}

export function ErrorBox({ message }: { message: string }) {
  if (!message) return null;
  return <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm font-medium text-rose-900"><AlertTriangle size={16} className="mt-0.5 shrink-0" />{message}</div>;
}

export function Spinner({ label }: { label: string }) {
  return <div className="flex items-center gap-3 py-10 text-ink-soft" role="status"><span className="h-5 w-5 animate-spin rounded-full border-2 border-brand-200 border-t-brand-700" />{label}</div>;
}
