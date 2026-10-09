import { FilePlus2, Star } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Complaint } from "../types";
import { ErrorBox, Spinner } from "../components/Badges";
import ComplaintCard from "../components/ComplaintCard";
import { EmptyIllustration } from "../components/Illustrations";

function Actions({ c, onDone }: { c: Complaint; onDone: () => void }) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<"" | "confirm" | "reopen">("");
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (c.status !== "resolved") {
    if (c.status === "closed" && c.rating) return <p className="inline-flex items-center gap-1 text-sm font-semibold">{t("complaint.rating")}: {Array.from({ length: c.rating }, (_, i) => <Star key={i} size={16} className="fill-saffron-400 text-saffron-500" />)}</p>;
    return null;
  }
  async function send() {
    setError(""); setBusy(true);
    try {
      if (mode === "confirm") await api(`/complaints/${c.id}/confirm`, { json: { rating, feedback: text.trim() || null } });
      else await api(`/complaints/${c.id}/reopen`, { json: { note: text.trim() } });
      onDone();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  if (!mode) return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="text-sm font-semibold text-teal-900">{t("complaint.needsYou")}</span>
      <button className="btn btn-primary" onClick={() => setMode("confirm")}>{t("complaint.confirm")}</button>
      <button className="btn btn-ghost" onClick={() => setMode("reopen")}>{t("complaint.reopen")}</button>
    </div>
  );
  return (
    <div className="space-y-3">
      {mode === "confirm" && (
        <div className="flex items-center gap-1 text-sm font-semibold">
          {t("complaint.rating")}:
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} type="button" aria-label={`${n}`} className="cursor-pointer p-0.5" onClick={() => setRating(n)}>
              <Star size={24} className={n <= rating ? "fill-saffron-400 text-saffron-500" : "text-slate-300"} />
            </button>
          ))}
        </div>
      )}
      <textarea className="input" rows={2} placeholder={mode === "confirm" ? t("complaint.feedback") : t("complaint.reopenNote")} value={text} onChange={(e) => setText(e.target.value)} />
      <ErrorBox message={error} />
      <div className="flex gap-2">
        <button className="btn btn-primary" disabled={busy || (mode === "reopen" && text.trim().length < 3)} onClick={send}>{t("complaint.send")}</button>
        <button className="btn btn-ghost" onClick={() => setMode("")}>{t("complaint.cancel")}</button>
      </div>
    </div>
  );
}

export default function MyComplaints() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<Complaint[] | null>(null);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const list = await api<Complaint[]>("/complaints/mine");
      setRows(await Promise.all(list.map((c) => api<Complaint>(`/complaints/${c.id}`))));
    } catch (e) { setError((e as Error).message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const OPEN = ["in_review", "assigned", "in_progress", "reopened"];
  const shown = (rows ?? []).filter((c) => filter === "all" || (filter === "open" ? OPEN.includes(c.status) : c.status === filter));
  const pills: [string, string][] = [["all", t("complaint.allStatus")], ["open", t("complaint.open")], ["resolved", t("status.resolved")], ["closed", t("status.closed")]];
  return (
    <div className="section max-w-4xl space-y-5 py-8 lg:py-10">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="mr-auto text-3xl sm:text-4xl">{t("nav.mine")}</h1>
        <Link to="/new" className="btn btn-primary"><FilePlus2 size={16} />{t("nav.new")}</Link>
      </div>
      <div className="flex flex-wrap gap-2" role="group">
        {pills.map(([k, label]) => (
          <button key={k} onClick={() => setFilter(k)} aria-pressed={filter === k}
            className={`cursor-pointer rounded-full border px-4 py-1.5 text-sm font-semibold transition ${filter === k ? "border-brand-700 bg-brand-700 text-white" : "border-line bg-white text-ink hover:border-brand-300"}`}>{label}</button>
        ))}
      </div>
      <ErrorBox message={error} />
      {!rows && !error && <Spinner label={t("common.loading")} />}
      {rows && shown.length === 0 && (
        <div className="card flex flex-col items-center py-10 text-center"><EmptyIllustration className="w-44" /><p className="mt-3 text-ink-soft">{t("complaint.emptyMine")}</p></div>
      )}
      <div className="space-y-4">{shown.map((c) => <ComplaintCard key={c.id} c={c}><Actions c={c} onDone={load} /></ComplaintCard>)}</div>
    </div>
  );
}
