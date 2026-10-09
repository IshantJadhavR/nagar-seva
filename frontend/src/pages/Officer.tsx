import { CheckCircle2, Clock3, HelpCircle, Hourglass, MapPinOff, Phone, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import type { Complaint } from "../types";
import { ErrorBox, Spinner } from "../components/Badges";
import ComplaintCard from "../components/ComplaintCard";
import { EmptyIllustration } from "../components/Illustrations";
import MapView from "../components/MapView";

function Work({ c, onDone }: { c: Complaint; onDone: () => void }) {
  const { t } = useTranslation();
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function move(status: string) {
    setError(""); setBusy(true);
    try { await api(`/officer/complaints/${c.id}/status`, { method: "PATCH", json: { status, note: note.trim() } }); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function wrongLocation() {
    setError(""); setBusy(true);
    try { await api(`/officer/complaints/${c.id}/wrong-location`, { json: { note: note.trim() } }); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  const wrongBtn = c.location_flag === "wrong"
    ? <span className="chip bg-amber-100 text-amber-900"><MapPinOff size={13} />{t("officer.wrongSent")}</span>
    : <button type="button" className="btn btn-ghost" disabled={busy} onClick={wrongLocation} title={t("officer.wrongHint")}><MapPinOff size={16} />{t("officer.wrong")}</button>;
  const [helpOpen, setHelpOpen] = useState(false);
  const [reason, setReason] = useState("");
  async function askHelp() {
    setError(""); setBusy(true);
    try { await api(`/officer/complaints/${c.id}/help`, { json: { reason: reason.trim() } }); setHelpOpen(false); setReason(""); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  const hr = c.help_request;
  const helpBlock = (
    <div className="space-y-2 text-sm">
      {hr?.status === "open" && <p className="chip bg-violet-100 text-violet-900"><HelpCircle size={13} />{t("officer.helpWaiting")}</p>}
      {hr?.status === "answered" && (
        <div className="rounded-xl border border-line bg-brand-50/60 p-3">
          <p className="font-semibold">{t("officer.helpAnswered")}</p>
          {hr.reply && <p className="mt-1 text-ink">{hr.reply}</p>}
          {c.citizen_phone && <a href={`tel:${c.citizen_phone}`} className="mt-2 inline-flex items-center gap-1.5 font-bold text-brand-800 hover:underline"><Phone size={15} />{c.citizen_phone}</a>}
          {hr.phone_shared && !c.citizen_phone && <p className="mt-1 text-ink-soft">{t("officer.phoneHidden")}</p>}
        </div>
      )}
      {(!hr || hr.status === "answered") && !helpOpen && (
        <button type="button" className="btn btn-ghost" onClick={() => setHelpOpen(true)}><HelpCircle size={16} />{t("officer.askHelp")}</button>
      )}
      {helpOpen && (
        <div className="space-y-2">
          <textarea className="input" rows={2} maxLength={500} placeholder={t("officer.helpReason")} value={reason} onChange={(e) => setReason(e.target.value)} />
          <div className="flex gap-2"><button type="button" className="btn btn-primary" disabled={busy || reason.trim().length < 5} onClick={askHelp}>{t("officer.sendHelp")}</button>
            <button type="button" className="btn btn-ghost" onClick={() => setHelpOpen(false)}>{t("common.cancel", "Cancel")}</button></div>
        </div>
      )}
    </div>
  );
  if (c.status === "assigned" || c.status === "reopened") {
    return (
      <div className="space-y-2"><ErrorBox message={error} />
        <textarea className="input" rows={1} placeholder={t("officer.wrongNote")} value={note} onChange={(e) => setNote(e.target.value)} />
        <div className="flex flex-wrap gap-3"><button className="btn btn-primary" disabled={busy} onClick={() => move("in_progress")}>{t("officer.start")}</button>{wrongBtn}</div>
        {helpBlock}
      </div>
    );
  }
  if (c.status === "in_progress") {
    return (
      <div className="space-y-3">
        <textarea className="input" rows={2} placeholder={t("officer.note")} value={note} onChange={(e) => setNote(e.target.value)} />
        <ErrorBox message={error} />
        <div className="flex flex-wrap gap-3"><button className="btn btn-primary" disabled={busy || !note.trim()} onClick={() => move("resolved")}>{t("officer.resolve")}</button>{wrongBtn}</div>
        {helpBlock}
      </div>
    );
  }
  return null;
}

export default function Officer() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<Complaint[] | null>(null);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const list = await api<Complaint[]>("/officer/complaints");
      setRows(await Promise.all(list.map((c) => api<Complaint>(`/complaints/${c.id}`))));
    } catch (e) { setError((e as Error).message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const all = rows ?? [];
  const n = (s: string) => all.filter((c) => c.status === s).length;
  const kpis = [[Hourglass, "kAssigned", n("assigned")], [Clock3, "kProgress", n("in_progress")], [CheckCircle2, "kResolved", n("resolved") + n("closed")], [RotateCcw, "kReopened", n("reopened")]] as const;
  const shown = all.filter((c) => filter === "all" || c.status === filter);
  const markers = shown.filter((c) => c.lat !== null && c.lng !== null)
    .map((c) => ({ lat: c.lat as number, lng: c.lng as number, label: `#${c.id} ${c.category} (${c.priority_level})` }));
  return (
    <div className="section space-y-6 py-8 lg:py-10">
      <header><h1 className="text-3xl sm:text-4xl">{t("officer.title")}</h1><p className="mt-2 text-ink-soft">{t("officer.sub")}</p></header>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map(([Icon, k, v]) => (
          <div key={k} className="card flex items-center gap-4 !p-4">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-100 text-brand-800"><Icon size={22} /></span>
            <div><p className="font-display text-3xl font-extrabold leading-none">{v}</p><p className="mt-1 text-sm text-ink-soft">{t(`officer.${k}`)}</p></div>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2" role="group">
        {["all", "assigned", "in_progress", "resolved", "reopened", "closed"].map((s) => (
          <button key={s} onClick={() => setFilter(s)} aria-pressed={filter === s}
            className={`cursor-pointer rounded-full border px-4 py-1.5 text-sm font-semibold transition ${filter === s ? "border-brand-700 bg-brand-700 text-white" : "border-line bg-white text-ink hover:border-brand-300"}`}>
            {s === "all" ? t("officer.all") : t(`status.${s}`)}</button>
        ))}
      </div>
      <ErrorBox message={error} />
      {!rows && !error && <Spinner label={t("common.loading")} />}
      {markers.length > 0 && <MapView markers={markers} height={240} />}
      {rows && shown.length === 0 && <div className="card flex flex-col items-center py-10 text-center"><EmptyIllustration className="w-44" /><p className="mt-3 text-ink-soft">{t("complaint.emptyOfficer")}</p></div>}
      <div className="space-y-4">{shown.map((c) => <ComplaintCard key={c.id} c={c}><Work c={c} onDone={load} /></ComplaintCard>)}</div>
    </div>
  );
}
