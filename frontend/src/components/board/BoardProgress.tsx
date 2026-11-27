import BaseProgressBar from "@/components/shared/BaseProgressBar";
import { boardProgress } from "@/lib/boardProgress";
import type { BoardColumn } from "@/types/api";

interface BoardProgressProps {
  columns: readonly BoardColumn[];
}

// Share of the Board's Cards that are in a "Done" Column.
export default function BoardProgress({ columns }: BoardProgressProps) {
  const progress = boardProgress(columns);

  return (
    <div className="flex w-full flex-col gap-1 sm:w-64">
      <span className="text-xs text-slate-500 tabular-nums">
        {progress.done} of {progress.total} cards done
      </span>
      <BaseProgressBar
        percent={progress.percent}
        label="Board progress"
        valueText={`${progress.done} of ${progress.total} cards done`}
      />
    </div>
  );
}
