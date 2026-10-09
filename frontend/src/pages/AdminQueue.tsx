import { ArrowRight, HelpCircle, MapPinned, Phone, Send, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import type { Complaint } from "../types";
import { ErrorBox, Spinner } from "../components/Badges";
import ComplaintCard from "../components/ComplaintCard";
import { EmptyIllustration } from "../components/Illustrations";
import MapView from "../components/MapView";

interface Cat { id: number; name: string; department: string }

function RouteBox({ c, cats, onDone }: { c: Complaint; cats: Cat[]; onDone: () => void }) {
  const { t } = useTranslation();
  const [cat, setCat] = useState(c.category);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const dept = cats.find((x) => x.name === cat)?.department;
  async function route() {
    setError(""); setBusy(true);
    try { await api(`/admin/complaints/${c.id}/route`, { json: { category: cat } }); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-ink-soft">{t("admin.model")}: <b className="text-ink">{t(`cat.${c.category_pred}`, c.category_pred)}</b> ({Math.round(c.confidence * 100)}%)</p>
      <div className="flex flex-wrap items-end gap-3">
        <div><label className="label" htmlFor={`cat${c.id}`}>{t("admin.chooseCategory")}</label>
          <select id={`cat${c.id}`} className="input !w-auto min-w-48" value={cat} onChange={(e) => setCat(e.target.value)}>
            {cats.map((x) => <option key={x.id} value={x.name}>{t(`cat.${x.name}`, x.name)}</option>)}
          </select></div>
        <span className="inline-flex items-center gap-1.5 pb-3 text-sm font-semibold text-brand-800"><ArrowRight size={16} />{dept}</span>
        <button className="btn btn-primary" disabled={busy} onClick={route}><Send size={16} />{t("admin.route")}</button>
      </div>
      <ErrorBox message={error} />
    </div>
  );
}

/** Admin answers the officer's help request; sharing the citizen's phone is an explicit, logged choice. */
function HelpReply({ c, onDone }: { c: Complaint; onDone: () => void }) {
  const { t } = useTranslation();
  const [msg, setMsg] = useState("");
  const [share, setShare] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const hr = c.help_request;
  if (!hr || hr.status !== "open") return null;
  async function send() {
    setError(""); setBusy(true);
    try { await api(`/admin/complaints/${c.id}/help-reply`, { json: { message: msg.trim(), share_phone: share } }); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <div className="space-y-3 rounded-xl border border-violet-200 bg-violet-50/60 p-4">
      <h4 className="flex items-center gap-2 text-base"><HelpCircle size={18} className="text-violet-700" />{t("admin.helpTitle")}</h4>
      <p className="text-sm"><b>{hr.by}:</b> {hr.reason}</p>
      <p className="flex items-center gap-1.5 text-sm text-ink-soft"><Phone size={14} />{c.citizen_phone ? <b className="text-ink">{c.citizen_phone}</b> : t("admin.noPhone")}</p>
      <textarea className="input" rows={2} maxLength={500} placeholder={t("admin.helpMsg")} value={msg} onChange={(e) => setMsg(e.target.value)} />
      <label className={`flex items-start gap-2 text-sm ${c.citizen_phone ? "" : "opacity-50"}`}>
        <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[#146461]" disabled={!c.citizen_phone} checked={share} onChange={(e) => setShare(e.target.checked)} />
        <span>{t("admin.sharePhone")}</span>
      </label>
      <ErrorBox message={error} />
      <button className="btn btn-primary" disabled={busy} onClick={send}><Send size={16} />{t("admin.sendReply")}</button>
    </div>
  );
}

/** "Delete" = reject with a reason. The record is kept for the audit trail and the citizen sees the reason. */
function RejectBox({ c, onDone }: { c: Complaint; onDone: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function reject() {
    setError(""); setBusy(true);
    try { await api(`/admin/complaints/${c.id}/reject`, { json: { reason: reason.trim() } }); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  if (!open) return <button type="button" className="btn btn-ghost !text-rose-800" onClick={() => setOpen(true)}><Trash2 size={16} />{t("admin.reject")}</button>;
  return (
    <div className="space-y-2 rounded-xl border border-rose-200 bg-rose-50/60 p-4">
      <p className="text-sm font-semibold text-rose-900">{t("admin.rejectHint")}</p>
      <textarea className="input" rows={2} maxLength={500} placeholder={t("admin.rejectReason")} value={reason} onChange={(e) => setReason(e.target.value)} />
      <ErrorBox message={error} />
      <div className="flex gap-2">
        <button className="btn btn-primary !bg-rose-700" disabled={busy || reason.trim().length < 5} onClick={reject}><Trash2 size={16} />{t("admin.rejectConfirm")}</button>
        <button className="btn btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel", "Cancel")}</button>
      </div>
    </div>
  );
}

function FixLocation({ c, onDone }: { c: Complaint; onDone: () => void }) {
  const { t } = useTranslation();
  const [pin, setPin] = useState<{ lat: number; lng: number } | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function save() {
    if (!pin) return;
    setError(""); setBusy(true);
    try { await api(`/admin/complaints/${c.id}/location`, { json: { lat: pin.lat, lng: pin.lng, note: note.trim() } }); onDone(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-ink-soft">{t("admin.fixHint")}</p>
      <MapView height={220} onPick={(lat, lng) => setPin({ lat, lng })} picked={pin ?? (c.lat !== null && c.lng !== null ? { lat: c.lat, lng: c.lng } : null)} />
      <input className="input" maxLength={500} placeholder={t("admin.fixNote")} value={note} onChange={(e) => setNote(e.target.value)} />
      <ErrorBox message={error} />
      <button className="btn btn-primary" disabled={busy || !pin} onClick={save}><MapPinned size={16} />{t("admin.fixSave")}</button>
      <HelpReply c={c} onDone={onDone} />
      <RejectBox c={c} onDone={onDone} />
    </div>
  );
}

export default function AdminQueue() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<Complaint[] | null>(null);
  const [locRows, setLocRows] = useState<Complaint[]>([]);
  const [cats, setCats] = useState<Cat[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [q, c] = await Promise.all([api<Complaint[]>("/admin/review-queue"), api<Cat[]>("/admin/categories")]);
      setCats(c);
      const lp = await api<Complaint[]>("/admin/location-problems");
      setLocRows(await Promise.all(lp.map((x) => api<Complaint>(`/complaints/${x.id}`))));
      setRows(await Promise.all(q.map((x) => api<Complaint>(`/complaints/${x.id}`))));
    } catch (e) { setError((e as Error).message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <div className="section max-w-4xl space-y-5 py-8 lg:py-10">
      <header><h1 className="text-3xl sm:text-4xl">{t("admin.queueTitle")}</h1><p className="mt-2 text-ink-soft">{t("admin.queueSub")}</p></header>
      <ErrorBox message={error} />
      {!rows && !error && <Spinner label={t("common.loading")} />}
      {rows?.length === 0 && <div className="card flex flex-col items-center py-10 text-center"><EmptyIllustration className="w-44" /><p className="mt-3 text-ink-soft">{t("admin.empty")}</p></div>}
      <div className="space-y-4">{rows?.map((c) => <ComplaintCard key={c.id} c={c} defaultOpen={c.urgent}><RouteBox c={c} cats={cats} onDone={load} /></ComplaintCard>)}</div>
      {locRows.length > 0 && (
        <section className="space-y-4 pt-4">
          <header><h2 className="text-2xl">{t("admin.locTitle")}</h2><p className="mt-1 text-ink-soft">{t("admin.locSub")}</p></header>
          {locRows.map((c) => <ComplaintCard key={c.id} c={c} defaultOpen><FixLocation c={c} onDone={load} /></ComplaintCard>)}
        </section>
      )}
    </div>
  );
}
