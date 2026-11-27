import BaseProgressBar from "@/components/shared/BaseProgressBar";
import { checklistProgress } from "@/lib/checklist";

interface ChecklistProgressProps {
  items: readonly { isDone: boolean }[];
}

// Progress bar for a Card's to-do list. Renders nothing for an empty list.
// The label row and the 40px bar row match a form field, so it lines up with
// the Title field next to it.
export default function ChecklistProgress({ items }: ChecklistProgressProps) {
  const progress = checklistProgress(items);
  if (!progress) return null;

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-slate-700">Progress</span>
      <div className="flex h-10 items-center">
        <div className="w-full">
          <BaseProgressBar
            percent={progress.percent}
            label="To-do progress"
            valueText={`${progress.done} of ${progress.total} done`}
          />
        </div>
      </div>
    </div>
  );
}
