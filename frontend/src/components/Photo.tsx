import { useEffect, useState, type ReactNode } from "react";

/** Public photos live in frontend/public/images/. If a file is missing the page still looks fine (fallback or nothing). */
export const PHOTOS = {
  hero: "/images/hero-office.jpg",
  pothole: "/images/pothole.jpg",
  drainage: "/images/drainage.jpg",
  garbage: "/images/garbage.jpg",
  streetlight: "/images/streetlight.jpg",
  water: "/images/water-leak.jpg",
} as const;

/** true = loaded, false = missing, null = still checking */
export function useImageExists(src: string): boolean | null {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    let live = true;
    const img = new Image();
    img.onload = () => live && setOk(true);
    img.onerror = () => live && setOk(false);
    img.src = src;
    return () => { live = false; };
  }, [src]);
  return ok;
}

export function Photo({ src, alt, className = "", fallback = null }: { src: string; alt: string; className?: string; fallback?: ReactNode }) {
  const ok = useImageExists(src);
  if (ok === false) return <>{fallback}</>;
  if (ok === null) return <div className={`animate-pulse bg-slate-200 ${className}`} aria-hidden />;
  return <img src={src} alt={alt} loading="lazy" decoding="async" className={className} />;
}
