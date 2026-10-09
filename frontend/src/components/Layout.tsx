import { BarChart3, BookOpen, FilePlus2, Inbox, ListChecks, LogIn, LogOut, MapPinned, Settings2, UserRound, UserPlus, type LucideProps } from "lucide-react";
import type { ComponentType } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth";
import { setLanguage } from "../i18n";

type LinkDef = [string, string, ComponentType<LucideProps>];

export default function Layout() {
  const { t, i18n } = useTranslation();
  const { session, logout } = useAuth();
  const links: LinkDef[] =
    session?.role === "citizen" ? [["/new", "nav.new", FilePlus2], ["/mine", "nav.mine", ListChecks]]
    : session?.role === "officer" ? [["/officer", "nav.assigned", ListChecks]]
    : session?.role === "admin" ? [["/admin/queue", "nav.queue", Inbox], ["/admin/analytics", "nav.analytics", BarChart3], ["/admin/settings", "nav.settings", Settings2]]
    : [];
  links.push(["/guide", "guide.navShort", BookOpen]);
  const cls = ({ isActive }: { isActive: boolean }) =>
    `inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition ${isActive ? "bg-brand-700 text-white" : "text-ink hover:bg-brand-50"}`;
  const lang = i18n.language === "hi" ? "hi" : "en";
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-line bg-white/90 backdrop-blur">
        <div className="section flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
          <Link to={session ? "/" : "/"} className="flex items-center gap-2.5" aria-label={t("app.title")}>
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-700 text-white"><MapPinned size={22} /></span>
            <span className="leading-tight">
              <span className="block font-display text-lg font-extrabold text-ink">{t("app.title")}</span>
              <span className="hidden text-xs font-medium text-ink-soft sm:block">{t("app.tagline")}</span>
            </span>
          </Link>
          <nav className="order-3 flex w-full flex-wrap gap-1 sm:order-none sm:ml-4 sm:w-auto" aria-label="Main">
            {links.map(([to, key, Icon]) => <NavLink key={to} to={to} className={cls}><Icon size={17} />{t(key)}</NavLink>)}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <div className="inline-flex rounded-xl border border-line bg-white p-0.5" role="group" aria-label={t("app.language")}>
              {(["en", "hi"] as const).map((l) => (
                <button key={l} onClick={() => setLanguage(l)} aria-pressed={lang === l}
                  className={`cursor-pointer rounded-[10px] px-2.5 py-1.5 text-sm font-bold transition ${lang === l ? "bg-ink text-white" : "text-ink hover:bg-slate-100"}`}>
                  {l === "en" ? "EN" : "हिन्दी"}
                </button>
              ))}
            </div>
            {session ? (
              <>
                <Link to="/profile" className="hidden items-center gap-2 rounded-xl border border-line bg-white px-3 py-2 text-sm font-semibold text-ink hover:bg-brand-50 sm:inline-flex" title={t("app.profile")}>
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-saffron-200 text-xs font-extrabold text-saffron-700">{session.name.trim().charAt(0).toUpperCase()}</span>
                  <span className="max-w-[9rem] truncate">{session.name}</span>
                </Link>
                <button className="btn btn-ghost" onClick={logout}><LogOut size={16} /><span className="hidden sm:inline">{t("app.logout")}</span></button>
              </>
            ) : (
              <>
                <Link to="/login?as=citizen" className="btn btn-ghost"><LogIn size={16} />{t("nav.login")}</Link>
                <Link to="/register" className="btn btn-primary hidden sm:inline-flex"><UserPlus size={16} />{t("nav.register")}</Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1"><Outlet /></main>
      <footer className="border-t border-line bg-white">
        <div className="section flex flex-wrap items-center gap-2 py-5 text-sm text-ink-soft">
          <UserRound size={15} className="hidden" /><span>{t("app.footer")}</span>
        </div>
      </footer>
    </div>
  );
}
