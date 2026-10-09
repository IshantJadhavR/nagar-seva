import { Bot, Camera, CheckCircle2, LocateFixed, Send, Sparkles, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Complaint, GeoResult, PhotoGps, Prediction } from "../types";
import { ErrorBox, PriorityBadge } from "../components/Badges";
import Breakdown from "../components/Breakdown";
import CategoryIcon from "../components/CategoryIcon";
import ComplaintCard from "../components/ComplaintCard";
import LocationPanel from "../components/LocationPanel";
import MapView from "../components/MapView";
import { haversineM } from "../lib/geo";

const Step = ({ n, title, children }: { n: number; title: string; children: React.ReactNode }) => (
  <section className="card">
    <h2 className="mb-4 flex items-center gap-3 text-xl"><span className="grid h-8 w-8 place-items-center rounded-full bg-brand-700 text-sm font-extrabold text-white">{n}</span>{title}</h2>
    {children}
  </section>
);

export default function NewComplaint() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [pin, setPin] = useState<{ lat: number; lng: number } | null>(null);
  const [address, setAddress] = useState("");
  const [ward, setWard] = useState("");
  const [flags, setFlags] = useState({ near_school: false, near_hospital: false, on_main_road: false });
  const [photo, setPhoto] = useState<File | null>(null);
  const [pred, setPred] = useState<Prediction | null>(null);
  const [done, setDone] = useState<Complaint | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<"" | "predict" | "submit">("");

  const [geo, setGeo] = useState<GeoResult | null>(null);
  const [geoBusy, setGeoBusy] = useState(false);
  const [photoGps, setPhotoGps] = useState<PhotoGps | null>(null);

  // Ask the server what is at this pin (debounced so dragging / typing does not spam the free map services)
  useEffect(() => {
    if (!pin) { setGeo(null); return; }
    let cancelled = false;
    setGeoBusy(true);
    const id = setTimeout(async () => {
      try {
        const r = await api<GeoResult>("/geo/check", { json: { lat: pin.lat, lng: pin.lng, address: address.trim() || null } });
        if (!cancelled) setGeo(r);
      } catch { if (!cancelled) setGeo(null); }
      finally { if (!cancelled) setGeoBusy(false); }
    }, 900);
    return () => { cancelled = true; clearTimeout(id); };
  }, [pin, address]);

  async function onPhoto(f: File | null) {
    setPhoto(f); setPhotoGps(null);
    if (!f) return;
    const form = new FormData();
    form.append("file", f);
    try { setPhotoGps(await api<PhotoGps>("/geo/photo-gps", { form })); } catch { /* optional check */ }
  }
  const photoDistance = pin && photoGps?.has_gps && photoGps.lat !== undefined && photoGps.lng !== undefined
    ? Math.round(haversineM(pin.lat, pin.lng, photoGps.lat, photoGps.lng)) : null;

  async function preview() {
    setError("");
    if (text.trim().length < 10) return setError(t("form.tooShort"));
    setBusy("predict");
    try { setPred(await api<Prediction>("/predict", { json: { text: text.trim() } })); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(""); }
  }

  function myLocation() {
    navigator.geolocation?.getCurrentPosition(
      (p) => setPin({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => setError(t("form.locationFail")),
    );
  }

  async function submit() {
    setError("");
    if (text.trim().length < 10) return setError(t("form.tooShort"));
    setBusy("submit");
    try {
      let c = await api<Complaint>("/complaints", {
        json: { text: text.trim(), lat: pin?.lat ?? null, lng: pin?.lng ?? null, address: address.trim() || null, ward: ward.trim() || null, ...flags },
      });
      if (photo) {
        const form = new FormData();
        form.append("file", photo);
        try {
          const r = await api<{ image_path: string }>(`/complaints/${c.id}/image`, { form });
          c = { ...c, image_path: r.image_path };
        } catch (e) { setError(t("form.photoFail") + (e as Error).message); }
      }
      setDone(c);
      setText(""); setPin(null); setAddress(""); setWard(""); setPhoto(null); setPhotoGps(null); setGeo(null); setPred(null);
      setFlags({ near_school: false, near_hospital: false, on_main_road: false });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(""); }
  }

  const flag = (k: keyof typeof flags, label: string) => (
    <label className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3.5 py-2.5 text-sm font-semibold transition ${flags[k] ? "border-brand-600 bg-brand-50 text-brand-900" : "border-line bg-white text-ink hover:border-brand-300"}`}>
      <input type="checkbox" className="h-4 w-4 accent-[#146461]" checked={flags[k]} onChange={(e) => setFlags({ ...flags, [k]: e.target.checked })} /> {label}
    </label>
  );

  return (
    <div className="section max-w-4xl space-y-6 py-8 lg:py-10">
      <header>
        <h1 className="text-3xl sm:text-4xl">{t("form.title")}</h1>
        <p className="mt-2 max-w-2xl text-ink-soft">{t("form.sub")} <Link to="/guide" className="font-semibold text-brand-700 hover:underline">{t("guide.link")}</Link></p>
      </header>

      {done && (
        <div className="space-y-3">
          <p role="status" className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 font-semibold text-emerald-900"><CheckCircle2 size={20} />{t("form.submitted")}
            <Link to="/mine" className="ml-auto text-sm text-emerald-900 underline">{t("nav.mine")}</Link></p>
          <ComplaintCard c={done} defaultOpen />
        </div>
      )}

      <Step n={1} title={t("form.step1")}>
        <label className="label" htmlFor="text">{t("form.text")}</label>
        <textarea id="text" rows={5} maxLength={2000} className="input" placeholder={t("form.placeholder")}
          value={text} onChange={(e) => { setText(e.target.value); setPred(null); }} />
        <p className="hint text-right">{text.length}/2000 {t("form.chars")}</p>
      </Step>

      <Step n={2} title={t("form.step2")}>
        <label className="label">{t("form.pin")}</label>
        <MapView height={300} onPick={(lat, lng) => setPin({ lat, lng })} picked={pin} />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button type="button" className="btn btn-ghost" onClick={myLocation}><LocateFixed size={16} />{t("form.myLocation")}</button>
          {pin && <span className="font-mono text-sm text-ink-soft">{pin.lat.toFixed(5)}, {pin.lng.toFixed(5)}</span>}
        </div>
        <LocationPanel geo={geo} loading={geoBusy} photo={photoGps} photoDistance={photoDistance}
          onUseAddress={setAddress} onUsePhotoPin={(lat, lng) => setPin({ lat, lng })} />
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div><label className="label" htmlFor="addr">{t("form.address")}</label><input id="addr" className="input" maxLength={300} value={address} onChange={(e) => setAddress(e.target.value)} /></div>
          <div><label className="label" htmlFor="ward">{t("form.ward")}</label><input id="ward" className="input" maxLength={40} placeholder="Ward-1" value={ward} onChange={(e) => setWard(e.target.value)} /></div>
        </div>
      </Step>

      <Step n={3} title={t("form.step3")}>
        <div className="flex flex-wrap gap-3">{flag("near_school", t("form.nearSchool"))}{flag("near_hospital", t("form.nearHospital"))}{flag("on_main_road", t("form.mainRoad"))}</div>
        <p className="hint">{t("form.flagsHint")}</p>
        <div className="mt-5">
          <label className="label" htmlFor="photo"><Camera size={15} className="mr-1.5 inline" />{t("form.photo")}</label>
          <input id="photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => onPhoto(e.target.files?.[0] ?? null)}
            className="block w-full cursor-pointer rounded-xl border border-dashed border-brand-300 bg-brand-50/50 p-3 text-sm file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-brand-700 file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-white" />
        </div>
      </Step>

      <ErrorBox message={error} />
      <div className="flex flex-wrap gap-3">
        <button className="btn btn-ghost btn-lg" onClick={preview} disabled={busy !== ""}><Sparkles size={18} />{busy === "predict" ? t("form.predicting") : t("form.preview")}</button>
        <button className="btn btn-primary btn-lg" onClick={submit} disabled={busy !== ""}><Send size={18} />{busy === "submit" ? t("form.submitting") : t("form.submit")}</button>
      </div>

      {pred && (
        <section className="card space-y-4" aria-live="polite">
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 text-lg font-bold"><CategoryIcon name={pred.category} className="text-brand-700" />{t(`cat.${pred.category}`, pred.category)}</span>
            <span className="text-ink-soft">{t("pred.confidence")}: <b className="text-ink">{Math.round(pred.confidence * 100)}%</b></span>
            <span className="text-ink-soft">{pred.department}</span>
            <PriorityBadge level={pred.priority_level} score={pred.priority_score} />
            <span className={`chip ${pred.would_auto_route ? "bg-emerald-100 text-emerald-900" : "bg-violet-100 text-violet-900"}`}>
              {pred.would_auto_route ? <Bot size={13} /> : <UserRound size={13} />}{pred.would_auto_route ? t("pred.autoRoute") : t("pred.review")}
            </span>
          </div>
          {pred.review_reasons.length > 0 && <p className="text-sm text-ink-soft"><b className="text-ink">{t("pred.why")}:</b> {pred.review_reasons.join("; ")}</p>}
          {pred.secondary_category && <p className="text-sm text-ink-soft">{t("pred.secondary")}: {t(`cat.${pred.secondary_category}`, pred.secondary_category)}</p>}
          <div className="space-y-1.5 text-sm">
            {pred.top3.map(([k, v]) => (
              <div key={k} className="flex items-center gap-3">
                <span className="w-32 shrink-0">{t(`cat.${k}`, k)}</span>
                <div className="h-2.5 flex-1 rounded-full bg-slate-100"><div className="h-2.5 rounded-full bg-brand-600" style={{ width: `${Math.round(v * 100)}%` }} /></div>
                <span className="w-10 text-right font-mono">{Math.round(v * 100)}%</span>
              </div>
            ))}
          </div>
          <div><h3 className="mb-2 text-base">{t("pred.breakdown")}</h3><Breakdown data={{ ...pred.priority_breakdown, critical_reason: pred.critical_reason }} /></div>
          <p className="hint">{t("form.previewNote")}</p>
        </section>
      )}
    </div>
  );
}
