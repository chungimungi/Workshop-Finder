import { motion } from "motion/react";
import type { Conference, Workshop } from "../types";
import { deadlineStatus, daysUntil } from "../types";

interface Props {
  workshop: Workshop;
  conference?: Conference;
  index: number;
  onTopicClick: (topic: string) => void;
}

const ISO_DATE = (iso: string | null) => {
  if (!iso) return "TBA";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "TBA";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

export function WorkshopRow({ workshop: w, conference, index, onTopicClick }: Props) {
  const status = deadlineStatus(w.deadline);
  const days = daysUntil(w.deadline);
  const mark = status === "closing" ? "!" : status === "open" ? " " : status === "tba" ? "?" : "·";
  const daysLabel =
    days === null ? "TBA" : days <= 0 ? "0d" : `${days}d`;

  return (
    <motion.tr
      className={status}
      layout
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.14 } }}
      transition={{ duration: 0.18, delay: Math.min(index * 0.012, 0.18) }}
    >
      <td className="col-mark row-mark" data-label="status" aria-label={`status: ${status}`}>
        {mark}
      </td>
      <td className="col-due cell-due" data-label="deadline">{ISO_DATE(w.deadline)}</td>
      <td className="col-days cell-days" data-label="days">{daysLabel}</td>
      <td className="col-rank cell-rank" data-label="rank">{conference?.rank ?? "—"}</td>
      <td className="col-venue cell-venue" data-label="venue">
        <span className="marquee-text">{w.conference}{w.year ? ` ${w.year}` : ""}</span>
      </td>
      <td className="col-name cell-name" data-label="workshop">
        <span className="marquee-text">
          <a href={w.url} target="_blank" rel="noreferrer">{w.name}</a>
        </span>
      </td>
      <td className="col-field cell-field" data-label="field">
        <span className="marquee-text">{conference?.field ?? "Unclassified"}</span>
      </td>
      <td className="col-topics cell-topics" data-label="topics">
        <span className="marquee-text">
          {w.topics.slice(0, 4).map((t) => (
            <button key={t} type="button" className="topic-btn" onClick={() => onTopicClick(t)}>
              {t}
            </button>
          ))}
        </span>
      </td>
    </motion.tr>
  );
}
