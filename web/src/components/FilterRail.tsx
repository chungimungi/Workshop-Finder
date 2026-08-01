import type { Conference, DeadlineStatus, Workshop } from "../types";
import type { Filters } from "../data";

interface Props {
  filters: Filters;
  onChange: (f: Filters) => void;
  conferences: Map<string, Conference>;
  workshops: Workshop[];
  topics: string[];
  statusCounts: Record<DeadlineStatus, number>;
  onToggleStatus: (s: DeadlineStatus) => void;
}

function toggleIn(set: Set<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

interface SectionSpec {
  id: string;
  label: string;
  options: { value: string; count: number }[];
  selected: Set<string>;
  toggle: (v: string) => void;
  open?: boolean;
  status?: boolean;
}

function Section({ spec }: { spec: SectionSpec }) {
  return (
    <details className="panel-section" open={spec.open}>
      <summary>
        <span className="toggle" aria-hidden="true" />
        <span>{spec.label}</span>
        <span className="ps-count">{spec.selected.size > 0 ? `${spec.selected.size} on` : ""}</span>
      </summary>
      <div className="ps-body">
        {spec.options.map((o) => (
          <button
            key={o.value}
            type="button"
            className={`opt${spec.status ? " status-opt" : ""}`}
            aria-pressed={spec.selected.has(o.value)}
            data-mark={spec.status ? o.value.toUpperCase().slice(0, 1) : undefined}
            onClick={() => spec.toggle(o.value)}
          >
            <span className="box" aria-hidden="true" />
            <span className="opt-label">{o.value}</span>
            <span className="opt-n">{o.count}</span>
          </button>
        ))}
      </div>
    </details>
  );
}

export function FilterPanel({ filters, onChange, conferences, workshops, topics, statusCounts, onToggleStatus }: Props) {
  const countBy = (key: (w: Workshop) => string | null) => {
    const m = new Map<string, number>();
    for (const w of workshops) {
      const k = key(w);
      if (k) m.set(k, (m.get(k) ?? 0) + 1);
    }
    return [...m.entries()].map(([value, count]) => ({ value, count })).sort((a, b) => b.count - a.count);
  };

  const fieldOptions = countBy((w) => conferences.get(w.conference)?.field ?? null).sort((a, b) =>
    a.value.localeCompare(b.value),
  );
  const confOptions = countBy((w) => w.conference);
  const rankOptions = countBy((w) => conferences.get(w.conference)?.rank ?? null);
  const topicOptions = topics.map((t) => ({ value: t, count: workshops.filter((w) => w.topics.includes(t)).length }));

  const statusOptions = (["closing", "open", "tba"] as DeadlineStatus[]).map((s) => ({
    value: s,
    count: statusCounts[s],
  }));

  const sections: SectionSpec[] = [
    {
      id: "status",
      label: "Status",
      options: statusOptions,
      selected: filters.statuses,
      toggle: (v) => onToggleStatus(v as DeadlineStatus),
      open: true,
      status: true,
    },
    {
      id: "field",
      label: "Field of research",
      options: fieldOptions,
      selected: filters.fields,
      toggle: (v) => onChange({ ...filters, fields: toggleIn(filters.fields, v) }),
      open: true,
    },
    {
      id: "topic",
      label: "Topic",
      options: topicOptions,
      selected: new Set(filters.topic ? [filters.topic] : []),
      toggle: (v) => onChange({ ...filters, topic: filters.topic === v ? null : v }),
    },
    {
      id: "conference",
      label: "Host conference",
      options: confOptions,
      selected: filters.conferences,
      toggle: (v) => onChange({ ...filters, conferences: toggleIn(filters.conferences, v) }),
    },
    {
      id: "rank",
      label: "Conference rank",
      options: rankOptions,
      selected: filters.ranks,
      toggle: (v) => onChange({ ...filters, ranks: toggleIn(filters.ranks, v) }),
    },
  ];

  return (
    <nav className="filter-panel" aria-label="Ledger filters">
      <div className="panel-head">Filters</div>
      {sections.map((s) => (
        <Section key={s.id} spec={s} />
      ))}
      <div className="panel-actions">
        <button
          type="button"
          onClick={() =>
            onChange({ ...filters, fields: new Set(), conferences: new Set(), ranks: new Set(), statuses: new Set(), topic: null })
          }
        >
          Clear
        </button>
      </div>
    </nav>
  );
}
