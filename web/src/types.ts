export interface Conference {
  acronym: string;
  title: string;
  rank: "A*" | "A";
  field: string;
  forCode: string;
  dblp: string | null;
}

export interface Workshop {
  id: string;
  name: string;
  shortName: string;
  workshopAcronym: string;
  conference: string;
  year: number | null;
  deadline: string | null; // ISO
  deadlineRaw: string | null;
  conferenceStart: string | null; // ISO
  location: string | null;
  website: string | null;
  openreviewUrl: string | null;
  url: string; // best link: website ?? openreviewUrl
  topics: string[];
  source: "openreview" | "website";
}

export type DeadlineStatus = "closing" | "open" | "tba" | "closed";

export interface Dataset {
  meta: {
    generatedAt: string;
    workshopCount: number;
    conferenceCount: number;
    sources: string[];
  };
  conferences: Conference[];
  workshops: Workshop[];
}

export const CLOSING_WINDOW_DAYS = 21;

export function deadlineStatus(deadline: string | null, now = new Date()): DeadlineStatus {
  if (!deadline) return "tba";
  const due = new Date(deadline).getTime();
  if (Number.isNaN(due)) return "tba";
  const diffDays = (due - now.getTime()) / 86_400_000;
  if (diffDays < 0) return "closed";
  if (diffDays <= CLOSING_WINDOW_DAYS) return "closing";
  return "open";
}

export function formatDeadline(iso: string | null): string {
  if (!iso) return "TBA";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "TBA";
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function daysUntil(iso: string | null, now = new Date()): number | null {
  if (!iso) return null;
  const diff = new Date(iso).getTime() - now.getTime();
  if (Number.isNaN(diff)) return null;
  return Math.ceil(diff / 86_400_000);
}
