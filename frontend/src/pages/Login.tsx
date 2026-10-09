import { Eye, EyeOff, Info, Lock, Mail, UserRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";
import { ROLES, ROLE_ICON, ROLE_STYLE, isRole, type RoleKey } from "../lib/roles";
import { useAuth } from "../auth";
import { ErrorBox } from "../components/Badges";
import { AuthIllustration } from "../components/Illustrations";
import { PHOTOS, Photo } from "../components/Photo";

const SHOW_DEMO = (import.meta.env.VITE_SHOW_DEMO as string | undefined) !== "false";
const DEMO: Record<RoleKey, string[][]> = {
  citizen: [["Citizen", "citizen@example.com", "Citizen@123"]],
  officer: [["Officer (Roads)", "public.officer1@example.com", "Officer@123"], ["Officer (Garbage)", "solid.officer1@example.com", "Officer@123"]],
  admin: [["Admin", "admin@example.com", "Admin@123"]],
};

/** One page for log in and sign up. Citizens create accounts here; officers and admins are created by the project team. */
export default function Login({ mode }: { mode: "login" | "register" }) {
  const { t } = useTranslation();
  const { login, register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isLogin = mode === "login";
  const [params, setParams] = useSearchParams();
  const asParam = params.get("as");
  const role: RoleKey = isRole(asParam) ? asParam : "citizen";
  const pick = (r: RoleKey) => { setParams({ as: r }, { replace: true }); setError(""); setEmail(""); setPassword(""); };

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      if (isLogin) await login(email.trim(), password, role);
      else await register(name.trim(), email.trim(), password, phone.trim());
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }

  return (
    <div className="section grid items-center gap-10 py-10 lg:grid-cols-2 lg:py-16">
      <div className="mx-auto w-full max-w-md">
        {isLogin && (
          <div role="tablist" aria-label={t("auth.whoAreYou")} className="mb-6 grid grid-cols-3 gap-2">
            {ROLES.map((r) => {
              const Icon = ROLE_ICON[r];
              const on = r === role;
              return (
                <button key={r} type="button" role="tab" aria-selected={on} onClick={() => pick(r)}
                  className={`flex cursor-pointer flex-col items-center gap-1.5 rounded-2xl border-2 px-2 py-3 text-sm font-bold transition ${on ? ROLE_STYLE[r].ring + " text-ink" : "border-line bg-white text-ink-soft hover:border-slate-300"}`}>
                  <span className={`grid h-9 w-9 place-items-center rounded-xl ${on ? ROLE_STYLE[r].icon : "bg-slate-100 text-slate-500"}`}><Icon size={19} /></span>
                  {t(`roles.${r}`)}
                </button>
              );
            })}
          </div>
        )}
        <h1 className="text-3xl sm:text-4xl">{isLogin ? t(`auth.loginAs.${role}`) : t("auth.createTitle")}</h1>
        <p className="mb-6 mt-2 text-ink-soft">{isLogin ? t(`auth.loginSub.${role}`) : t("auth.createSub")}</p>
        <form onSubmit={submit} className="card space-y-4">
          {!isLogin && (
            <div><label className="label" htmlFor="name">{t("auth.name")}</label>
              <div className="relative"><UserRound size={18} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input id="name" className="input !pl-10" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></div></div>
          )}
          <div><label className="label" htmlFor="email">{t("auth.email")}</label>
            <div className="relative"><Mail size={18} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input id="email" type="email" className="input !pl-10" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div></div>
          {!isLogin && (
            <div><label className="label" htmlFor="phone">{t("auth.phone")}</label>
              <input id="phone" type="tel" inputMode="numeric" className="input" autoComplete="tel" maxLength={16} value={phone} onChange={(e) => setPhone(e.target.value)} />
              <p className="hint">{t("auth.phoneHint")}</p></div>
          )}
          <div><label className="label" htmlFor="pw">{t("auth.password")}</label>
            <div className="relative"><Lock size={18} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input id="pw" type={show ? "text" : "password"} className="input !px-10" autoComplete={isLogin ? "current-password" : "new-password"}
                value={password} onChange={(e) => setPassword(e.target.value)} required minLength={isLogin ? 1 : 8} />
              <button type="button" onClick={() => setShow(!show)} aria-label={show ? t("auth.hidePw") : t("auth.showPw")}
                className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer rounded-lg p-1.5 text-slate-500 hover:bg-slate-100">{show ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
            {!isLogin && <p className="hint">{t("auth.passwordHint")}</p>}</div>
          <ErrorBox message={error} />
          <button className="btn btn-primary btn-lg w-full" disabled={busy}>{isLogin ? t("auth.login") : t("auth.register")}</button>
          {isLogin && role !== "citizen" && <p className="rounded-xl bg-slate-50 px-3.5 py-2.5 text-center text-sm text-ink-soft">{t("auth.staffNote")}</p>}
          {(!isLogin || role === "citizen") && (
            <p className="text-center text-sm text-ink-soft">
              {isLogin ? t("auth.noAccount") : t("auth.haveAccount")}{" "}
              <Link to={isLogin ? "/register" : "/login?as=citizen"} className="font-bold text-brand-700 hover:underline">{isLogin ? t("auth.register") : t("auth.login")}</Link>
            </p>
          )}
          {!isLogin && <p className="text-center text-sm text-ink-soft">{t("auth.staffAsk")} <Link to="/login?as=officer" className="font-bold text-brand-700 hover:underline">{t("auth.staffLogin")}</Link></p>}
          <p className="text-center text-sm"><Link to="/guide" className="font-semibold text-brand-700 hover:underline">{t("guide.link")}</Link></p>
        </form>
        {SHOW_DEMO && isLogin && (
          <details className="mt-4 rounded-2xl border border-saffron-200 bg-saffron-50 p-4 text-sm">
            <summary className="flex cursor-pointer items-center gap-2 font-semibold text-saffron-700"><Info size={16} />{t("auth.demo")}</summary>
            <ul className="mt-3 space-y-2">
              {DEMO[role].map(([label, mail, pw]) => (
                <li key={mail}>
                  <button type="button" className="w-full cursor-pointer rounded-lg bg-white px-3 py-2 text-left hover:bg-saffron-100" onClick={() => { setEmail(mail); setPassword(pw); }}>
                    <b>{label}</b><br /><span className="font-mono text-xs text-ink-soft">{mail} · {pw}</span>
                  </button>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
      <div className="hidden lg:block">
        <Photo src={PHOTOS.pothole} alt="" className="mx-auto aspect-[4/3] w-full max-w-md rounded-3xl object-cover shadow-xl"
          fallback={<AuthIllustration className="mx-auto w-full max-w-md" />} />
        <h2 className="mx-auto mt-6 max-w-md text-2xl">{t("auth.sideTitle")}</h2>
        <p className="mx-auto mt-1 max-w-md text-ink-soft">{t("auth.sideSub")}</p>
      </div>
    </div>
  );
}
