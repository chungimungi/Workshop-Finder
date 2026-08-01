import type { Conference, Dataset, DeadlineStatus, Workshop } from "./types";
import { deadlineStatus } from "./types";

export async function loadDataset(): Promise<Dataset> {
  const res = await fetch(`${import.meta.env.BASE_URL}data/dataset.json`);
  if (!res.ok) throw new Error(`Failed to load dataset (${res.status})`);
  const data: Dataset = await res.json();
  // Safety net: never surface closed or past-host workshops, even if the
  // static JSON was built before a conference date slipped by.
  const upcoming = data.workshops.filter((w) => isUpcoming(w));
  const used = new Set(upcoming.map((w) => w.conference));
  return {
    ...data,
    workshops: upcoming,
    conferences: data.conferences.filter((c) => used.has(c.acronym)),
    meta: { ...data.meta, workshopCount: upcoming.length, conferenceCount: used.size },
  };
}

/** Keep closing / open / TBA — drop closed deadlines and past host conferences. */
export function isUpcoming(w: Workshop, now = new Date()): boolean {
  if (w.deadline) {
    const due = new Date(w.deadline);
    if (!Number.isNaN(due.getTime()) && due.getTime() < now.getTime()) return false;
  }
  if (w.conferenceStart) {
    const start = new Date(w.conferenceStart);
    if (!Number.isNaN(start.getTime()) && start.getTime() < now.getTime()) return false;
  }
  if (w.year != null && w.year < now.getFullYear() && !w.deadline) return false;
  return true;
}

export interface Filters {
  query: string;
  fields: Set<string>;
  conferences: Set<string>;
  ranks: Set<string>;
  statuses: Set<DeadlineStatus>;
  topic: string | null;
}

export const emptyFilters = (): Filters => ({
  query: "",
  fields: new Set(),
  conferences: new Set(),
  ranks: new Set(),
  statuses: new Set(),
  topic: null,
});

export function isActive(f: Filters): boolean {
  return (
    f.query.trim() !== "" ||
    f.fields.size > 0 ||
    f.conferences.size > 0 ||
    f.ranks.size > 0 ||
    f.statuses.size > 0 ||
    f.topic !== null
  );
}

const STOPWORDS = new Set([
  "workshop", "on", "the", "and", "for", "of", "in", "at", "a", "an", "to", "first", "second",
  "third", "1st", "2nd", "3rd", "4th", "5th", "international", "ieee", "acm", "2026", "2027",
]);

function queryTokens(query: string): string[] {
  return query
    .toLowerCase()
    .split(/[^a-z0-9+#]+/)
    .filter((t) => t.length > 1 && !STOPWORDS.has(t));
}

export function workshopHaystack(w: Workshop, conf?: Conference): string {
  return [
    w.name,
    w.shortName,
    w.workshopAcronym,
    w.conference,
    conf?.title ?? "",
    w.topics.join(" "),
    conf?.field ?? "",
    w.location ?? "",
  ]
    .join(" ")
    .toLowerCase();
}

export function applyFilters(
  workshops: Workshop[],
  conferences: Map<string, Conference>,
  f: Filters,
): Workshop[] {
  const tokens = queryTokens(f.query);
  return workshops.filter((w) => {
    const conf = conferences.get(w.conference);
    if (f.fields.size > 0 && !f.fields.has(conf?.field ?? "Unclassified")) return false;
    if (f.conferences.size > 0 && !f.conferences.has(w.conference)) return false;
    if (f.ranks.size > 0 && !f.ranks.has(conf?.rank ?? "")) return false;
    if (f.statuses.size > 0 && !f.statuses.has(deadlineStatus(w.deadline))) return false;
    if (f.topic && !w.topics.includes(f.topic)) return false;
    if (tokens.length > 0) {
      const hay = workshopHaystack(w, conf);
      if (!tokens.every((t) => hay.includes(t))) return false;
    }
    return true;
  });
}

const statusRank: Record<DeadlineStatus, number> = { closing: 0, open: 1, tba: 2, closed: 3 };

export function sortByDeadline(workshops: Workshop[]): Workshop[] {
  return [...workshops].sort((a, b) => {
    const sa = statusRank[deadlineStatus(a.deadline)];
    const sb = statusRank[deadlineStatus(b.deadline)];
    if (sa !== sb) return sa - sb;
    if (a.deadline && b.deadline) return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    if (a.deadline) return -1;
    if (b.deadline) return 1;
    return a.name.localeCompare(b.name);
  });
}
