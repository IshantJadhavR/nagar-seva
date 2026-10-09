import { Construction, CircleHelp, Droplets, HeartPulse, Lightbulb, Store, Trash2, Waves, type LucideProps } from "lucide-react";
import type { ComponentType } from "react";

export const CATEGORY_ICON: Record<string, ComponentType<LucideProps>> = {
  Roads: Construction, Garbage: Trash2, "Water Supply": Droplets, Drainage: Waves,
  Streetlight: Lightbulb, "Public Health": HeartPulse, Encroachment: Store, Other: CircleHelp,
};
export const CATEGORIES = ["Roads", "Garbage", "Water Supply", "Drainage", "Streetlight", "Public Health", "Encroachment", "Other"];

export default function CategoryIcon({ name, size = 18, className = "" }: { name: string; size?: number; className?: string }) {
  const Icon = CATEGORY_ICON[name] ?? CircleHelp;
  return <Icon size={size} className={className} aria-hidden />;
}
