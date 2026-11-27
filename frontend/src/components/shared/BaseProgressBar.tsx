interface BaseProgressBarProps {
  // Whole number from 0 to 100.
  percent: number;
  label: string;
  // Spoken value, for example "3 of 5 done".
  valueText: string;
}

// A horizontal bar with the percentage written next to it. It turns green at 100%.
export default function BaseProgressBar({
  percent,
  label,
  valueText,
}: BaseProgressBarProps) {
  const isComplete = percent === 100;

  return (
    <div className="flex items-center gap-2.5">
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-valuetext={valueText}
        className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-slate-200"
      >
        <div
          style={{ width: `${percent}%` }}
          className={`h-full rounded-full transition-[width] duration-300 ${
            isComplete ? "bg-emerald-500" : "bg-indigo-600"
          }`}
        />
      </div>
      <span className="w-10 text-right text-sm font-medium text-slate-700 tabular-nums">
        {percent}%
      </span>
    </div>
  );
}
