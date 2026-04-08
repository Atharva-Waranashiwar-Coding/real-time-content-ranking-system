type PaginationControlsProps = {
  offset: number;
  limit: number;
  hasMore: boolean;
  onPrevious: () => void;
  onNext: () => void;
};

export function PaginationControls({
  offset,
  limit,
  hasMore,
  onPrevious,
  onNext,
}: PaginationControlsProps) {
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-[24px] border border-[color:var(--border-subtle)] bg-[color:var(--surface-strong)]/90 px-5 py-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--ink-soft)]">
          Feed pagination
        </p>
        <p className="mt-1 text-sm text-[color:var(--ink-soft)]">
          Page {currentPage} · Offset {offset}
        </p>
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onPrevious}
          disabled={offset === 0}
          className="rounded-full border border-[color:var(--border-subtle)] px-4 py-2 text-sm font-semibold text-[color:var(--ink-strong)] transition disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!hasMore}
          className="rounded-full bg-[color:var(--ink-strong)] px-4 py-2 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
