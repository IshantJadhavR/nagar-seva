import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { ErrorBox, Spinner } from "../components/Badges";
import { formatIST } from "../lib/time";

interface Me { phone?: string | null; name: string; email: string; role: string; department: string | null; ward: string | null; created_at: string }

export default function Profile() {
  const { t } = useTranslation();
  const [me, setMe] = useState<Me | null>(null);
  const [cur, setCur] = useState(""); const [nw, setNw] = useState("");
  const [phone, setPhone] = useState(""); const [phoneMsg, setPhoneMsg] = useState("");
  const [msg, setMsg] = useState(""); const [error, setError] = useState("");
  useEffect(() => { api<Me>("/auth/me").then((m) => { setMe(m); setPhone(m.phone ?? ""); }).catch((e) => setError((e as Error).message)); }, []);
  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setMsg("");
    try { await api("/auth/password", { json: { current_password: cur, new_password: nw } }); setMsg(t("profile.done")); setCur(""); setNw(""); }
    catch (err) { setError((err as Error).message); }
  }
  async function savePhone(e: FormEvent) {
    e.preventDefault(); setError(""); setPhoneMsg("");
    try { await api("/auth/phone", { method: "PUT", json: { phone: phone.trim() || null } }); setPhoneMsg(t("profile.phoneSaved")); }
    catch (err) { setError((err as Error).message); }
  }
  if (!me) return <div className="section py-8">{error ? <ErrorBox message={error} /> : <Spinner label={t("common.loading")} />}</div>;
  const rows: [string, string | null][] = [["auth.name", me.name], ["auth.email", me.email], ["profile.role", t(`roles.${me.role}`, me.role)],
    ["profile.dept", me.department], ["profile.ward", me.ward], ["profile.joined", formatIST(me.created_at, false)]];
  return (
    <div className="section grid gap-6 py-8 md:grid-cols-2">
      <div className="card">
        <h1 className="mb-4 text-2xl">{t("profile.title")}</h1>
        <dl className="divide-y divide-line">
          {rows.filter(([, v]) => v).map(([k, v]) => <div key={k} className="flex justify-between gap-4 py-2.5"><dt className="text-ink-soft">{t(k)}</dt><dd className="text-right font-semibold">{v}</dd></div>)}
        </dl>
      </div>
      {me.role === "citizen" && (
        <form onSubmit={savePhone} className="card space-y-4 md:col-span-2">
          <h2 className="text-2xl">{t("profile.phoneTitle")}</h2>
          <p className="text-ink-soft">{t("auth.phoneHint")}</p>
          <div className="max-w-sm"><label className="label" htmlFor="ph">{t("auth.phone")}</label>
            <input id="ph" type="tel" inputMode="numeric" className="input" maxLength={16} value={phone} onChange={(e) => setPhone(e.target.value)} /></div>
          {phoneMsg && <p role="status" className="rounded-xl bg-emerald-50 px-3.5 py-2.5 text-sm font-semibold text-emerald-900">{phoneMsg}</p>}
          <button className="btn btn-primary">{t("profile.phoneSave")}</button>
        </form>
      )}
      <form onSubmit={submit} className="card space-y-4">
        <h2 className="text-2xl">{t("profile.pwTitle")}</h2>
        <div><label className="label" htmlFor="cur">{t("profile.current")}</label><input id="cur" type="password" className="input" value={cur} onChange={(e) => setCur(e.target.value)} required autoComplete="current-password" /></div>
        <div><label className="label" htmlFor="nw">{t("profile.new")}</label><input id="nw" type="password" className="input" value={nw} onChange={(e) => setNw(e.target.value)} required minLength={8} autoComplete="new-password" /><p className="hint">{t("auth.passwordHint")}</p></div>
        <ErrorBox message={error} />
        {msg && <p role="status" className="rounded-xl bg-emerald-50 px-3.5 py-2.5 text-sm font-semibold text-emerald-900">{msg}</p>}
        <button className="btn btn-primary">{t("profile.update")}</button>
      </form>
    </div>
  );
}
