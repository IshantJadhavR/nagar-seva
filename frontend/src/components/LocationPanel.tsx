import { AlertTriangle, Camera, Hospital, MapPin, Route, School, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { GeoResult, PhotoGps } from "../types";

const Chip = ({ icon: Icon, label, tone }: { icon: typeof School; label: string; tone: string }) => (
  <span className={`chip ${tone}`}><Icon size={13} />{label}</span>
);

/** Shows what the map knows about the pin: address, nearby school / hospital / main road, and warnings. */
export default function LocationPanel({ geo, loading, photo, photoDistance, onUseAddress, onUsePhotoPin }: {
  geo: GeoResult | null; loading: boolean; photo: PhotoGps | null; photoDistance: number | null;
  onUseAddress: (a: string) => void; onUsePhotoPin: (lat: number, lng: number) => void;
}) {
  const { t } = useTranslation();
  const n = geo?.nearby;
  const near = (p: { distance_m: number } | null | undefined, max: number) => !!p && p.distance_m <= max;
  return (
    <div className="mt-4 space-y-3" aria-live="polite">
      {loading && <p className="hint">{t("geo.checking")}</p>}
      {geo && geo.inside_area === false && (
        <p role="alert" className="flex items-start gap-2 rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-900"><AlertTriangle size={18} className="mt-0.5 shrink-0" />{t("geo.outside")}</p>
      )}
      {geo?.geo_address && (
        <div className="rounded-xl border border-line bg-brand-50/50 p-3 text-sm">
          <p className="flex items-start gap-2"><MapPin size={16} className="mt-0.5 shrink-0 text-brand-700" /><span><b>{t("geo.mapSays")}:</b> {geo.geo_address}</span></p>
          <button type="button" className="mt-2 cursor-pointer text-sm font-semibold text-brand-700 hover:underline" onClick={() => onUseAddress(geo.geo_address as string)}>{t("geo.useAddress")}</button>
        </div>
      )}
      {geo?.address_mismatch && (
        <p role="alert" className="flex items-start gap-2 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900"><AlertTriangle size={18} className="mt-0.5 shrink-0" />
          {t("geo.mismatch", { km: ((geo.address_distance_m ?? 0) / 1000).toFixed(1) })}</p>
      )}
      {n && (
        <div className="flex flex-wrap items-center gap-2">
          {near(n.school, 300) && <Chip icon={School} tone="bg-amber-100 text-amber-900" label={t("geo.school", { d: n.school!.distance_m }) + (n.school!.name ? ` · ${n.school!.name}` : "")} />}
          {near(n.hospital, 300) && <Chip icon={Hospital} tone="bg-rose-100 text-rose-900" label={t("geo.hospital", { d: n.hospital!.distance_m }) + (n.hospital!.name ? ` · ${n.hospital!.name}` : "")} />}
          {near(n.main_road, 30) && <Chip icon={Route} tone="bg-sky-100 text-sky-900" label={t("geo.mainRoad")} />}
          {geo && geo.points_from_map === 0 && <span className="hint !mt-0 inline-flex items-center gap-1"><ShieldCheck size={14} />{t("geo.nothing")}</span>}
        </div>
      )}
      {geo && geo.points_from_map > 0 && <p className="hint !mt-0">{t("geo.priorityNote", { p: geo.points_from_map })}</p>}
      {geo && !geo.nearby_checked && geo.inside_area && !loading && <p className="hint !mt-0">{t("geo.unavailable")}</p>}
      {photo && !photo.has_gps && <p className="hint !mt-0 inline-flex items-center gap-1"><Camera size={14} />{t("geo.photoNoGps")}</p>}
      {photo?.has_gps && photo.lat !== undefined && photo.lng !== undefined && (
        <div className="rounded-xl border border-line p-3 text-sm">
          <p className="flex items-start gap-2"><Camera size={16} className="mt-0.5 shrink-0 text-brand-700" /><span><b>{t("geo.photoSays")}:</b> {photo.address ?? `${photo.lat.toFixed(5)}, ${photo.lng.toFixed(5)}`}</span></p>
          {photoDistance !== null && photoDistance > 300 && <p className="mt-1 font-semibold text-amber-900">{t("geo.photoFar", { m: photoDistance >= 1000 ? (photoDistance / 1000).toFixed(1) + " km" : photoDistance + " m" })}</p>}
          <button type="button" className="mt-2 cursor-pointer font-semibold text-brand-700 hover:underline" onClick={() => onUsePhotoPin(photo.lat as number, photo.lng as number)}>{t("geo.usePhotoPin")}</button>
        </div>
      )}
    </div>
  );
}
