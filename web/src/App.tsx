import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { applyFilters, emptyFilters, isActive, loadDataset, sortByDeadline, type Filters } from "./data";
import type { Conference, Dataset, DeadlineStatus, Workshop } from "./types";
import { deadlineStatus } from "./types";
import { WorkshopRow } from "./components/WorkshopCard";
import { FilterPanel } from "./components/FilterRail";
import { StatsPanel } from "./components/StatsPanel";

function toggleStatus(filters: Filters, status: DeadlineStatus): Filters {
  const next = new Set(filters.statuses);
  if (next.has(status)) next.delete(status);
  else next.add(status);
  return { ...filters, statuses: next };
}

/** Toggle CSS marquee on single-line cells whose text overflows the column. */
function applyMarquee() {
  const cells = document.querySelectorAll<HTMLElement>(".ledger-table tbody td.cell-name, .ledger-table tbody td.cell-topics, .ledger-table tbody td.cell-venue, .ledger-table tbody td.cell-field");
  cells.forEach((td) => {
    const text = td.querySelector<HTMLElement>(".marquee-text");
    if (!text) return;
    const overflow = text.scrollWidth - td.clientWidth;
    if (overflow > 2) {
      td.classList.add("marquee");
      td.style.setProperty("--marquee-travel", `-${overflow}px`);
      td.style.setProperty("--marquee-dur", `${Math.max(5, Math.min(20, overflow / 24))}s`);
    } else {
      td.classList.remove("marquee");
      td.style.removeProperty("--marquee-travel");
      td.style.removeProperty("--marquee-dur");
    }
  });
}

export default function App() {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [showStats, setShowStats] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    loadDataset()
      .then(setDataset)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load the ledger."));
  }, []);

  const conferences = useMemo(
    () => new Map<string, Conference>((dataset?.conferences ?? []).map((c) => [c.acronym, c])),
    [dataset],
  );

  const topics = useMemo(() => {
    const set = new Set<string>();
    for (const w of dataset?.workshops ?? []) for (const t of w.topics) set.add(t);
    return [...set].sort();
  }, [dataset]);

  const statusCounts = useMemo(() => {
    const counts: Record<DeadlineStatus, number> = { closing: 0, open: 0, tba: 0, closed: 0 };
    for (const w of dataset?.workshops ?? []) counts[deadlineStatus(w.deadline)] += 1;
    return counts;
  }, [dataset]);

  const visible: Workshop[] = useMemo(() => {
    if (!dataset) return [];
    return sortByDeadline(applyFilters(dataset.workshops, conferences, filters));
  }, [dataset, conferences, filters]);

  const openCount = statusCounts.closing + statusCounts.open;

  const resizeTimer = useRef<number | undefined>(undefined);
  useEffect(() => {
    const raf = requestAnimationFrame(applyMarquee);
    const onResize = () => {
      window.clearTimeout(resizeTimer.current);
      resizeTimer.current = window.setTimeout(applyMarquee, 120);
    };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      window.clearTimeout(resizeTimer.current);
    };
  }, [visible, showStats, sidebarOpen]);

  return (
    <MotionConfig reducedMotion="user">
      <header className="titlebar">
        <h1>Workshop Finder</h1>
        <span className="tb-meta">
          A*/A conferences · <b>deadlines first</b>
        </span>
      </header>

      <div className="promptbar" role="search">
        <span className="prompt-glyph" aria-hidden="true">&gt;_</span>
        <span className="prompt-field">
          <input
            type="search"
            value={filters.query}
            onChange={(e) => setFilters({ ...filters, query: e.target.value })}
            placeholder="interpretability, robotics, multimodal…"
            aria-label="Search workshops by topic, field, or keyword"
          />
          {filters.query !== "" && (
            <button type="button" className="clear-btn" onClick={() => setFilters({ ...filters, query: "" })}>
              clear
            </button>
          )}
        </span>
      </div>

      <div className={`ledger-body${sidebarOpen ? "" : " sidebar-closed"}`}>
        <FilterPanel
          filters={filters}
          onChange={setFilters}
          conferences={conferences}
          workshops={dataset?.workshops ?? []}
          topics={topics}
          statusCounts={statusCounts}
          onToggleStatus={(s) => setFilters(toggleStatus(filters, s))}
        />

        <main className="main-pane">
          <div className="status-bar">
            <button
              type="button"
              className="tool-btn sidebar-toggle"
              aria-pressed={sidebarOpen}
              aria-label={sidebarOpen ? "Collapse filters" : "Show filters"}
              onClick={() => setSidebarOpen((v) => !v)}
            >
              {sidebarOpen ? "« Filters" : "Filters »"}
            </button>
            <span className="result-line" role="status">
              {error
                ? <>READ ERROR — {error}</>
                : dataset
                  ? <><b>{visible.length}</b> row{visible.length === 1 ? "" : "s"} · {openCount} accepting submissions</>
                  : "READING LEDGER…"}
            </span>
            <span className="spacer" />
            {isActive(filters) && (
              <button type="button" className="tool-btn" onClick={() => setFilters(emptyFilters())}>
                Reset
              </button>
            )}
            <button
              type="button"
              className="tool-btn"
              aria-pressed={showStats}
              onClick={() => setShowStats((v) => !v)}
            >
              Stats
            </button>
          </div>

          <AnimatePresence initial={false}>
            {showStats && dataset && (
              <motion.div
                key="stats"
                className="stats-window"
                initial={{ opacity: 0, height: 0, overflow: "hidden" }}
                animate={{ opacity: 1, height: "auto", transitionEnd: { overflow: "visible" } }}
                exit={{ opacity: 0, height: 0, overflow: "hidden" }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="sw-head">Ledger summary</div>
                <StatsPanel workshops={visible} conferences={conferences} />
              </motion.div>
            )}
          </AnimatePresence>

          {dataset && visible.length === 0 && (
            <div className="empty-state">
              <strong>NO ROWS MATCH</strong>
              Loosen a filter, or try a broader keyword — the ledger only shows upcoming A*/A workshops.
            </div>
          )}

          <div className="ledger-scroll">
            <table className="ledger-table">
              <thead>
                <tr>
                  <th className="col-mark" scope="col" aria-label="Status">!</th>
                  <th className="col-due" scope="col">Deadline</th>
                  <th className="col-days" scope="col">Days</th>
                  <th className="col-rank" scope="col">Rank</th>
                  <th className="col-venue" scope="col">Venue</th>
                  <th className="col-name" scope="col">Workshop</th>
                  <th className="col-field" scope="col">Field</th>
                  <th className="col-topics" scope="col">Topics</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence mode="popLayout">
                  {visible.map((w, i) => (
                    <WorkshopRow
                      key={w.id}
                      workshop={w}
                      conference={conferences.get(w.conference)}
                      index={i}
                      onTopicClick={(t) => setFilters({ ...filters, topic: filters.topic === t ? null : t })}
                    />
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </main>
      </div>

      <footer className="ledger-footer">
        <div>
          {dataset && (
            <span className="lf-meta">
              {dataset.meta.workshopCount} workshops · {dataset.meta.conferenceCount} A*/A conferences ·
              refreshed {new Date(dataset.meta.generatedAt).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}
              {" — "}
            </span>
          )}
          sources: <a href="https://openreview.net">OpenReview</a> · <a href="https://portal.core.edu.au/conf-ranks/">ICORE2026</a> · conference websites — rebuilt by CI.
        </div>
      </footer>
    </MotionConfig>
  );
}
