import type { Conference, Workshop } from "../types";
import { deadlineStatus } from "../types";

interface Props {
  workshops: Workshop[];
  conferences: Map<string, Conference>;
}

const BLOCK = "\u2588";
const BAR_WIDTH = 20;

interface BarRow {
  label: string;
  value: number;
}

function AsciiBars({ rows }: { rows: BarRow[] }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <div>
      {rows.map((r) => {
        const filled = Math.round((r.value / max) * BAR_WIDTH);
        return (
          <div className="asciibar" key={r.label}>
            <span className="ab-label" title={r.label}>{r.label}</span>
            <span className="ab-track" aria-label={`${r.value} of ${max}`}>
              <span className="ab-fill">{BLOCK.repeat(filled)}</span>
              <span className="ab-empty">{BLOCK.repeat(Math.max(0, BAR_WIDTH - filled))}</span>
            </span>
            <span className="ab-value">{r.value}</span>
          </div>
        );
      })}
    </div>
  );
}

export function StatsPanel({ workshops, conferences }: Props) {
  const open = workshops.filter((w) => {
    const s = deadlineStatus(w.deadline);
    return s === "open" || s === "closing";
  });

  const byMonth = new Map<string, number>();
  for (const w of open) {
    if (!w.deadline) continue;
    const d = new Date(w.deadline);
    const key = d.toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
    byMonth.set(key, (byMonth.get(key) ?? 0) + 1);
  }
  const monthRows: BarRow[] = [...byMonth.entries()]
    .sort((a, b) => new Date(`1 ${a[0]}`).getTime() - new Date(`1 ${b[0]}`).getTime())
    .slice(0, 8)
    .map(([label, value]) => ({ label, value }));

  const closing = workshops.filter((w) => deadlineStatus(w.deadline) === "closing");

  const byField = new Map<string, number>();
  for (const w of workshops) {
    const f = conferences.get(w.conference)?.field ?? "Unclassified";
    byField.set(f, (byField.get(f) ?? 0) + 1);
  }
  const fieldRows: BarRow[] = [...byField.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([label, value]) => ({ label, value }));

  const byConf = new Map<string, number>();
  for (const w of workshops) byConf.set(w.conference, (byConf.get(w.conference) ?? 0) + 1);
  const confRows: BarRow[] = [...byConf.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([label, value]) => ({ label, value }));

  return (
    <div className="stats-grid">
      <div className="stats-cell">
        <h3>Deadlines by month <span className="sh-count">({open.length} open)</span></h3>
        {monthRows.length > 0 ? <AsciiBars rows={monthRows} /> : <p className="stats-empty">No dated deadlines in this view.</p>}
      </div>
      <div className="stats-cell">
        <h3>Closing within 21 days <span className="sh-count">({closing.length})</span></h3>
        {closing.length > 0 ? (
          <ul className="closing-list">
            {closing
              .sort((a, b) => new Date(a.deadline!).getTime() - new Date(b.deadline!).getTime())
              .map((w) => (
                <li key={w.id}>
                  <span className="cl-date">
                    {new Date(w.deadline!).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                  </span>
                  <span className="cl-name">{w.shortName || w.workshopAcronym}</span>
                </li>
              ))}
          </ul>
        ) : (
          <p className="stats-empty">Nothing closing soon in this view.</p>
        )}
      </div>
      <div className="stats-cell">
        <h3>Rows by field</h3>
        <AsciiBars rows={fieldRows} />
      </div>
      <div className="stats-cell">
        <h3>Busiest host conferences</h3>
        <AsciiBars rows={confRows} />
      </div>
    </div>
  );
}
