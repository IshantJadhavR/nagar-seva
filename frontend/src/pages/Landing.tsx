import { ArrowRight, BookOpen, Eye, FileText, Lock, ShieldCheck, Sparkles, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import CategoryIcon, { CATEGORIES } from "../components/CategoryIcon";
import { HeroIllustration } from "../components/Illustrations";
import { PHOTOS, Photo, useImageExists } from "../components/Photo";
import { ROLES, ROLE_ICON, ROLE_STYLE } from "../lib/roles";

const HOME: Record<string, string> = { citizen: "/new", officer: "/officer", admin: "/admin/queue" };

/** Faint photo behind the closing call-to-action. */
function BandPhoto() {
  const ok = useImageExists(PHOTOS.hero);
  if (!ok) return null;
  return (
    <>
      <img src={PHOTOS.hero} alt="" aria-hidden className="absolute inset-0 h-full w-full object-cover opacity-30" />
      <span className="absolute inset-0 bg-gradient-to-r from-brand-900 via-brand-800/90 to-brand-800/60" aria-hidden />
    </>
  );
}

/** Small floating cards over the hero photo, only when the photo is there. They show what the system does. */
function HeroBadges() {
  const { t } = useTranslation();
  const ok = useImageExists(PHOTOS.hero);
  if (!ok) return null;
  return (
    <>
      <div className="absolute -bottom-5 -left-3 hidden w-60 rounded-2xl border border-line bg-white p-3.5 shadow-xl sm:block">
        <p className="text-xs font-semibold text-ink-soft">{t("landing.badge.a1")}</p>
        <p className="mt-1 flex flex-wrap items-center gap-1.5 text-sm font-bold"><span className="chip bg-orange-200 text-orange-950">{t("prio.high")}</span><span className="chip bg-sky-100 text-sky-900">{t("status.assigned")}</span></p>
        <p className="mt-1.5 text-xs text-ink-soft">{t("landing.badge.a2")}</p>
      </div>
      <div className="absolute -right-3 top-6 hidden rounded-2xl border border-line bg-white px-4 py-3 shadow-xl sm:block">
        <p className="font-display text-2xl font-extrabold text-brand-800">EN · हिन्दी</p>
        <p className="text-xs font-semibold text-ink-soft">{t("landing.badge.b")}</p>
      </div>
    </>
  );
}

const CAT_OF = { pothole: "Roads", drainage: "Drainage", garbage: "Garbage", streetlight: "Streetlight", water: "Water Supply" } as const;
const GALLERY = [["pothole", "pothole"], ["drainage", "drainage"], ["garbage", "garbage"], ["streetlight", "streetlight"], ["water", "water"]] as const;

/** Real-life problems people report. Shown only if at least the first photo file exists. */
function Gallery() {
  const { t } = useTranslation();
  const any = useImageExists(PHOTOS.pothole);
  if (!any) return null;
  return (
    <section className="section py-16 lg:py-20" aria-labelledby="gal-h">
      <p className="eyebrow mb-2">{t("landing.photo.eyebrow")}</p>
      <h2 id="gal-h" className="mb-3 max-w-2xl text-3xl sm:text-4xl">{t("landing.photo.title")}</h2>
      <p className="mb-8 max-w-2xl text-ink-soft">{t("landing.photo.sub")}</p>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        {GALLERY.map(([key, label], i) => (
          <li key={key} className={`group relative overflow-hidden rounded-2xl ${i < 2 ? "lg:col-span-3" : "lg:col-span-2"}`}>
            <Photo src={PHOTOS[key]} alt={t(`landing.photo.${label}`)} className={`w-full object-cover transition duration-500 group-hover:scale-105 ${i < 2 ? "aspect-[16/10]" : "aspect-[4/3]"}`} />
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 via-black/50 to-transparent p-4 pt-12 text-white">
              <p className="flex items-center gap-2 font-display text-base font-bold"><CategoryIcon name={CAT_OF[key]} size={17} className="text-saffron-200" />{t(`landing.photo.${label}`)}</p>
              <p className="mt-1 text-xs italic text-white/85">“{t(`landing.quote.${key}`)}”</p>
              <p className="mt-1.5 text-[11px] font-semibold uppercase tracking-wide text-saffron-200">{t(`landing.dept.${key}`)}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Landing() {
  const { t } = useTranslation();
  const { session } = useAuth();
  const [stats, setStats] = useState<{ total: number; resolved: number; auto_routed: number } | null>(null);
  useEffect(() => { api<{ total: number; resolved: number; auto_routed: number }>("/public/stats").then(setStats).catch(() => setStats(null)); }, []);
  const steps = [
    [FileText, "s1t", "s1d"], [Sparkles, "s2t", "s2d"], [Wrench, "s3t", "s3d"],
  ] as const;
  const trust = [[ShieldCheck, "t1t", "t1d"], [Eye, "t2t", "t2d"], [Lock, "t3t", "t3d"]] as const;
  return (
    <>
      <section className="bg-gradient-to-b from-brand-50 to-canvas">
        <div className="section grid items-center gap-10 py-14 lg:grid-cols-2 lg:py-20">
          <div>
            <p className="eyebrow mb-4">{t("landing.eyebrow")}</p>
            <h1 className="text-4xl leading-[1.1] sm:text-5xl lg:text-6xl">{t("landing.h1")}</h1>
            <p className="mt-5 max-w-xl text-lg text-ink-soft">{t("landing.sub")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              {session ? (
                <Link to={HOME[session.role]} className="btn btn-accent btn-lg">{t("landing.ctaGo")}<ArrowRight size={18} /></Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-accent btn-lg">{t("landing.cta")}<ArrowRight size={18} /></Link>
                  <Link to="/login?as=citizen" className="btn btn-ghost btn-lg">{t("landing.cta2")}</Link>
                  <Link to="/guide" className="btn btn-ghost btn-lg"><BookOpen size={18} />{t("guide.navShort")}</Link>
                </>
              )}
            </div>
            {stats && (
              <dl className="mt-10 grid max-w-lg grid-cols-3 gap-4 border-t border-line pt-6">
                {([["statTotal", stats.total], ["statDone", stats.resolved], ["statAuto", stats.auto_routed]] as const).map(([k, v]) => (
                  <div key={k}><dt className="text-sm text-ink-soft">{t(`landing.${k}`)}</dt><dd className="font-display text-3xl font-extrabold text-brand-800">{v}</dd></div>
                ))}
              </dl>
            )}
          </div>
          <div className="relative mx-auto w-full max-w-xl">
            <Photo src={PHOTOS.hero} alt={t("landing.photo.hero")} className="aspect-[3/2] w-full rounded-3xl object-cover shadow-2xl ring-1 ring-black/5"
              fallback={<HeroIllustration className="mx-auto w-full max-w-xl drop-shadow-xl" />} />
            <HeroBadges />
          </div>
        </div>
      </section>

      {!session && (
        <section className="section py-14 lg:py-16" aria-labelledby="roles-h">
          <p className="eyebrow mb-2">{t("landing.rolesEyebrow")}</p>
          <h2 id="roles-h" className="mb-3 max-w-2xl text-3xl sm:text-4xl">{t("landing.rolesTitle")}</h2>
          <p className="mb-8 max-w-2xl text-ink-soft">{t("landing.rolesSub")}</p>
          <div className="grid gap-6 md:grid-cols-3">
            {ROLES.map((r) => {
              const Icon = ROLE_ICON[r];
              const can = t(`landing.role.${r}.can`, { returnObjects: true }) as string[];
              return (
                <article key={r} className="card flex flex-col">
                  <span className={`mb-4 grid h-12 w-12 place-items-center rounded-xl ${ROLE_STYLE[r].icon}`}><Icon size={24} /></span>
                  <h3 className="text-2xl">{t(`roles.${r}`)}</h3>
                  <p className="mt-1 text-ink-soft">{t(`landing.role.${r}.who`)}</p>
                  <ul className="my-4 flex-1 space-y-2 text-sm">
                    {can.map((x) => <li key={x} className="flex gap-2"><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${ROLE_STYLE[r].icon}`} />{x}</li>)}
                  </ul>
                  <div className="flex flex-wrap gap-2">
                    <Link to={`/login?as=${r}`} className="btn btn-primary">{t(`landing.role.${r}.login`)}</Link>
                    {r === "citizen" && <Link to="/register" className="btn btn-ghost">{t("nav.register")}</Link>}
                  </div>
                  {r !== "citizen" && <p className="hint">{t("auth.staffNote")}</p>}
                </article>
              );
            })}
          </div>
          <Link to="/guide" className="mt-6 inline-flex items-center gap-2 font-bold text-brand-700 hover:underline"><BookOpen size={18} />{t("guide.link")}</Link>
        </section>
      )}

      <Gallery />

      <section className="section py-16 lg:py-20">
        <p className="eyebrow mb-2">{t("landing.howEyebrow")}</p>
        <h2 className="mb-10 max-w-2xl text-3xl sm:text-4xl">{t("landing.howTitle")}</h2>
        <ol className="grid gap-6 md:grid-cols-3">
          {steps.map(([Icon, tk, dk], i) => (
            <li key={tk} className="card relative">
              <span className="absolute right-5 top-4 font-display text-5xl font-extrabold text-brand-100">{i + 1}</span>
              <span className="mb-4 grid h-12 w-12 place-items-center rounded-xl bg-brand-700 text-white"><Icon size={24} /></span>
              <h3 className="mb-1.5 text-xl">{t(`landing.${tk}`)}</h3>
              <p className="text-ink-soft">{t(`landing.${dk}`)}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="bg-white">
        <div className="section py-16 lg:py-20">
          <p className="eyebrow mb-2">{t("landing.catEyebrow")}</p>
          <h2 className="mb-10 text-3xl sm:text-4xl">{t("landing.catTitle")}</h2>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {CATEGORIES.map((c) => (
              <li key={c} className="flex items-start gap-3 rounded-2xl border border-line bg-canvas p-4">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-saffron-100 text-saffron-700"><CategoryIcon name={c} size={22} /></span>
                <div><p className="font-display font-bold">{t(`cat.${c}`)}</p><p className="text-sm text-ink-soft">{t(`catDesc.${c}`)}</p></div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section py-16 lg:py-20">
        <p className="eyebrow mb-2">{t("landing.trustEyebrow")}</p>
        <h2 className="mb-10 text-3xl sm:text-4xl">{t("landing.trustTitle")}</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {trust.map(([Icon, tk, dk]) => (
            <div key={tk}><Icon className="mb-3 text-brand-700" size={28} /><h3 className="mb-1.5 text-xl">{t(`landing.${tk}`)}</h3><p className="text-ink-soft">{t(`landing.${dk}`)}</p></div>
          ))}
        </div>
      </section>

      {!session && (
        <section className="section pb-20">
          <div className="relative flex flex-col items-start justify-between gap-6 overflow-hidden rounded-3xl bg-brand-800 p-8 text-white sm:flex-row sm:items-center sm:p-12">
            <BandPhoto />
            <div className="relative"><h2 className="!text-white text-3xl">{t("landing.finalTitle")}</h2><p className="mt-2 text-brand-100">{t("landing.finalSub")}</p></div>
            <Link to="/register" className="btn btn-accent btn-lg relative shrink-0">{t("nav.register")}<ArrowRight size={18} /></Link>
          </div>
        </section>
      )}
    </>
  );
}
