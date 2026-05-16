import { useSearchParams } from "react-router-dom";

import type { Candidate } from "@/api/candidates";
import { colorForCandidate } from "@/lib/colors";
import { compareByLean } from "@/lib/lean";
import {
  type CandidateSelection,
  parseCandidateSelection,
  writeCandidateSelection,
} from "@/lib/url-state";
import { t } from "@/i18n";

interface CandidateFilterProps {
  candidates: Candidate[];
}

export function CandidateFilter({ candidates }: CandidateFilterProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const selection: CandidateSelection = parseCandidateSelection(searchParams.get("candidates"));
  const allIds = candidates.map((c) => c.id);

  function setSelection(next: CandidateSelection) {
    const params = new URLSearchParams(searchParams);
    writeCandidateSelection(params, next);
    setSearchParams(params, { replace: true });
  }

  function toggle(id: number) {
    // Resolve the effective set: null (all) → start from every id; otherwise use the explicit list.
    const effective = selection === null ? allIds : selection;
    const next = effective.includes(id)
      ? effective.filter((x) => x !== id)
      : [...effective, id].sort((a, b) => a - b);
    // If toggling lands us back on "all", normalise to null so the URL stays clean.
    if (next.length === allIds.length) {
      setSelection(null);
    } else {
      setSelection(next);
    }
  }

  // For the checkbox UI: null = all checked, [] = none checked, [...] = those checked.
  const checkedSet = new Set<number>(selection === null ? allIds : selection);
  const isAllSelected = selection === null;
  const isNoneSelected = selection !== null && selection.length === 0;

  const eligibles = candidates.filter((c) => c.eligible).sort(compareByLean);
  const ineligibles = candidates.filter((c) => !c.eligible).sort(compareByLean);

  return (
    <section className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-700">{t.filters.candidates}</h2>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="text-xs text-indigo-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-300"
            onClick={() => setSelection(null)}
            disabled={isAllSelected}
          >
            {t.filters.selectAll}
          </button>
          <span aria-hidden className="text-slate-300">|</span>
          <button
            type="button"
            className="text-xs text-indigo-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-300"
            onClick={() => setSelection([])}
            disabled={isNoneSelected}
          >
            {t.filters.clearAll}
          </button>
        </div>
      </div>
      <CandidateGroup
        title={t.filters.eligible}
        candidates={eligibles}
        checkedSet={checkedSet}
        onToggle={toggle}
      />
      {ineligibles.length > 0 && (
        <CandidateGroup
          title={t.filters.ineligible}
          candidates={ineligibles}
          checkedSet={checkedSet}
          onToggle={toggle}
          muted
        />
      )}
    </section>
  );
}

interface CandidateGroupProps {
  title: string;
  candidates: Candidate[];
  checkedSet: Set<number>;
  onToggle: (id: number) => void;
  muted?: boolean;
}

function CandidateGroup({ title, candidates, checkedSet, onToggle, muted }: CandidateGroupProps) {
  return (
    <div className="mb-3 last:mb-0">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</h3>
      <ul className="space-y-1">
        {candidates.map((c) => {
          const checked = checkedSet.has(c.id);
          return (
            <li key={c.id}>
              <label
                className={`flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-slate-50 ${
                  muted ? "text-slate-500" : "text-slate-800"
                }`}
              >
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  checked={checked}
                  onChange={() => onToggle(c.id)}
                />
                <span
                  aria-hidden
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: colorForCandidate(c.id) }}
                />
                <span className="text-sm">{c.display_name}</span>
                {c.party && <span className="ml-auto text-xs text-slate-400">{c.party}</span>}
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
