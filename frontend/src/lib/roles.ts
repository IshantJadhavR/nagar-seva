import { Landmark, ShieldCheck, UserRound, type LucideProps } from "lucide-react";
import type { ComponentType } from "react";

export type RoleKey = "citizen" | "officer" | "admin";
export const ROLES: RoleKey[] = ["citizen", "officer", "admin"];
export const ROLE_ICON: Record<RoleKey, ComponentType<LucideProps>> = { citizen: UserRound, officer: Landmark, admin: ShieldCheck };
/** Tailwind classes per role so a person can recognise "which door" they are at. */
export const ROLE_STYLE: Record<RoleKey, { chip: string; icon: string; ring: string }> = {
  citizen: { chip: "bg-brand-100 text-brand-900", icon: "bg-brand-700 text-white", ring: "border-brand-600 bg-brand-50" },
  officer: { chip: "bg-sky-100 text-sky-900", icon: "bg-sky-700 text-white", ring: "border-sky-600 bg-sky-50" },
  admin: { chip: "bg-violet-100 text-violet-900", icon: "bg-violet-700 text-white", ring: "border-violet-600 bg-violet-50" },
};
export const isRole = (v: string | null): v is RoleKey => v === "citizen" || v === "officer" || v === "admin";
