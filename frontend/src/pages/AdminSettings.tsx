import { Check } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { ErrorBox, Spinner } from "../components/Badges";
import CategoryIcon from "../components/CategoryIcon";

interface Cat { id: number; name: string; department_id: number; department: string }
interface Dept { id: number; name: string }
interface Officer { id: number; name: string; email: string; department_id: number; ward: string | null }

export default function AdminSettings() {
  const { t } = useTranslation();
  const [cats, setCats] = useState<Cat[] | null>(null);
  const [depts, setDepts] = useState<Dept[]>([]);
  const [officers, setOfficers] = useState<Officer[]>([]);
  const [saved, setSaved] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api<Cat[]>("/admin/categories"), api<Dept[]>("/admin/departments"), api<Officer[]>("/admin/officers")])
      .then(([c, d, o]) => { setCats(c); setDepts(d); setOfficers(o); }).catch((e) => setError((e as Error).message));
  }, []);

  async function change(c: Cat, department_id: number) {
    setError(""); setSaved(null);
    try {
      const r = await api<Cat>(`/admin/categories/${c.id}`, { method: "PATCH", json: { department_id } });
      setCats((prev) => (prev ?? []).map((x) => (x.id === c.id ? r : x)));
      setSaved(c.id);
    } catch (e) { setError((e as Error).message); }
  }

  if (!cats) return <div className="section py-8">{error ? <ErrorBox message={error} /> : <Spinner label={t("common.loading")} />}</div>;
  return (
    <div className="section max-w-5xl space-y-8 py-8 lg:py-10">
      <section className="card space-y-4">
        <header><h1 className="text-2xl sm:text-3xl">{t("admin.mapping")}</h1><p className="mt-1 text-ink-soft">{t("admin.mappingHint")}</p></header>
        <ErrorBox message={error} />
        <ul className="divide-y divide-line">
          {cats.map((c) => (
            <li key={c.id} className="flex flex-wrap items-center gap-3 py-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-saffron-100 text-saffron-700"><CategoryIcon name={c.name} /></span>
              <span className="min-w-40 font-display font-bold">{t(`cat.${c.name}`, c.name)}</span>
              <select aria-label={c.name} className="input !w-auto min-w-64" value={c.department_id} onChange={(e) => change(c, Number(e.target.value))}>
                {depts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              {saved === c.id && <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-800"><Check size={16} />{t("admin.saved")}</span>}
            </li>
          ))}
        </ul>
      </section>
      <section className="card space-y-3">
        <header><h2 className="text-2xl">{t("admin.officersTitle")}</h2><p className="mt-1 text-ink-soft">{t("admin.officersHint")}</p></header>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr className="border-b-2 border-line text-ink"><th className="py-2 pr-3">{t("auth.name")}</th><th className="pr-3">{t("auth.email")}</th><th className="pr-3">{t("officer.dept")}</th><th>{t("officer.ward")}</th></tr></thead>
            <tbody>{officers.map((o) => (
              <tr key={o.id} className="border-b border-line last:border-0"><td className="py-2 pr-3 font-semibold">{o.name}</td><td className="pr-3 font-mono text-xs">{o.email}</td>
                <td className="pr-3">{depts.find((d) => d.id === o.department_id)?.name}</td><td>{o.ward}</td></tr>))}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
