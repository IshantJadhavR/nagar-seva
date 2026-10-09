import { ArrowRight, CheckCircle2, Lightbulb } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";
import { StatusBadge } from "../components/Badges";
import { ROLES, ROLE_ICON, ROLE_STYLE, isRole, type RoleKey } from "../lib/roles";

interface Step { t: string; d: string }
const STATUSES = ["in_review", "assigned", "in_progress", "resolved", "reopened", "closed", "rejected"];

/** Public, plain-language help for new users: who is who, what to click, what each word means. */
export default function Guide() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const p = params.get("for");
  const role: RoleKey = isRole(p) ? p : "citizen";
  const steps = t(`guide.${role}.steps`, { returnObjects: true }) as Step[];
  const tips = t(`guide.${role}.tips`, { returnObjects: true }) as string[];
  const faq = t("guide.faq", { returnObjects: true }) as { q: string; a: string }[];
  const prio = t("guide.priorities", { returnObjects: true }) as { k: string; d: string }[];
  return (
    <div className="section max-w-4xl space-y-10 py-8 lg:py-12">
      <header>
        <p className="eyebrow mb-2">{t("guide.eyebrow")}</p>
        <h1 className="text-3xl sm:text-4xl">{t("guide.title")}</h1>
        <p className="mt-3 max-w-2xl text-lg text-ink-soft">{t("guide.intro")}</p>
      </header>

      <section aria-labelledby="who-h">
        <h2 id="who-h" className="mb-4 text-2xl">{t("guide.whoTitle")}</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {ROLES.map((r) => {
            const Icon = ROLE_ICON[r];
            return (
              <button key={r} type="button" onClick={() => setParams({ for: r }, { replace: true })} aria-pressed={r === role}
                className={`card cursor-pointer text-left transition ${r === role ? "!border-2 " + ROLE_STYLE[r].ring : "hover:border-slate-300"}`}>
                <span className={`mb-3 grid h-11 w-11 place-items-center rounded-xl ${ROLE_STYLE[r].icon}`}><Icon size={22} /></span>
                <h3 className="text-xl">{t(`roles.${r}`)}</h3>
                <p className="mt-1 text-sm text-ink-soft">{t(`guide.who.${r}`)}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section aria-labelledby="steps-h">
        <h2 id="steps-h" className="mb-1 text-2xl">{t(`guide.${role}.title`)}</h2>
        <p className="mb-5 text-ink-soft">{t("guide.pickHint")}</p>
        <ol className="space-y-4">
          {steps.map((s, i) => (
            <li key={s.t} className="card flex gap-4 !p-5">
              <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-extrabold ${ROLE_STYLE[role].icon}`}>{i + 1}</span>
              <div><h3 className="text-lg">{s.t}</h3><p className="mt-1 text-ink-soft">{s.d}</p></div>
            </li>
          ))}
        </ol>
        <div className="mt-5 rounded-2xl border border-saffron-200 bg-saffron-50 p-5">
          <h3 className="mb-2 flex items-center gap-2 text-lg text-saffron-700"><Lightbulb size={18} />{t("guide.tipsTitle")}</h3>
          <ul className="space-y-1.5 text-sm">{tips.map((x) => <li key={x} className="flex gap-2"><CheckCircle2 size={16} className="mt-0.5 shrink-0 text-saffron-700" />{x}</li>)}</ul>
        </div>
        <Link to={role === "citizen" ? "/register" : `/login?as=${role}`} className="btn btn-accent btn-lg mt-6">{t(`guide.cta.${role}`)}<ArrowRight size={18} /></Link>
      </section>

      <section aria-labelledby="status-h">
        <h2 id="status-h" className="mb-4 text-2xl">{t("guide.statusTitle")}</h2>
        <dl className="card divide-y divide-line !p-0">
          {STATUSES.map((s) => (
            <div key={s} className="flex flex-col gap-1 px-5 py-3 sm:flex-row sm:items-center sm:gap-4">
              <dt className="sm:w-40"><StatusBadge status={s} /></dt>
              <dd className="text-sm text-ink-soft">{t(`guide.status.${s}`)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="prio-h">
        <h2 id="prio-h" className="mb-2 text-2xl">{t("guide.prioTitle")}</h2>
        <p className="mb-4 text-ink-soft">{t("guide.prioIntro")}</p>
        <ul className="grid gap-3 sm:grid-cols-2">
          {prio.map((x) => <li key={x.k} className="rounded-2xl border border-line bg-white p-4"><b>{x.k}</b><p className="mt-1 text-sm text-ink-soft">{x.d}</p></li>)}
        </ul>
      </section>

      <section aria-labelledby="faq-h">
        <h2 id="faq-h" className="mb-4 text-2xl">{t("guide.faqTitle")}</h2>
        <div className="space-y-2">
          {faq.map((f) => (
            <details key={f.q} className="card !p-4">
              <summary className="cursor-pointer font-semibold">{f.q}</summary>
              <p className="mt-2 text-ink-soft">{f.a}</p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
