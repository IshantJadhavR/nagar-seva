/** The server sends UTC ("...+00:00"). We always show Indian Standard Time, whatever the computer's clock says. */
const TZ = "Asia/Kolkata";

export function formatIST(iso: string, withTime = true): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: TZ, day: "2-digit", month: "short", year: "numeric",
    ...(withTime ? { hour: "numeric", minute: "2-digit", hour12: true } : {}),
  }).format(d).replace(/\bam\b/, "AM").replace(/\bpm\b/, "PM") + (withTime ? " IST" : "");
}

export function shortDayIST(isoDate: string): string {
  // isoDate is a calendar day like "2026-10-08" (already an Indian day, computed by the server)
  const d = new Date(isoDate + "T00:00:00+05:30");
  return new Intl.DateTimeFormat("en-IN", { timeZone: TZ, day: "numeric", month: "short" }).format(d);
}

export function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}
