"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import BaseInput from "@/components/shared/BaseInput";
import useBoardContext from "@/hooks/useBoardContext";
import { filterCardsByTitle } from "@/lib/boardSearch";

export default function BoardSidebar() {
  const pathname = usePathname();
  const { board, boardId, setOpenCardId } = useBoardContext();
  const [query, setQuery] = useState<string>("");

  const basePath = `/boards/${boardId}`;
  const navItems: readonly { href: string; label: string }[] = [
    { href: basePath, label: "Board" },
    { href: `${basePath}/activity`, label: "Activity" },
    { href: `${basePath}/analytics`, label: "Analytics" },
    { href: `${basePath}/settings`, label: "Board settings" },
  ];
  const results = board ? filterCardsByTitle(board.columns, query) : [];
  const hasQuery = query.trim().length > 0;

  return (
    <aside
      aria-label="Board sidebar"
      className="shrink-0 border-b-2 border-[#211621] bg-[#c9b7ef] p-3 lg:w-64 lg:border-r-2 lg:border-b-0"
    >
      <div className="flex flex-col gap-4 lg:sticky lg:top-[77px] lg:max-h-[calc(100vh-93px)] lg:overflow-y-auto">
        <p className="truncate px-2 text-sm font-semibold text-slate-900">
          {board?.name ?? "Board"}
        </p>
        <nav
          aria-label="Board pages"
          className="flex flex-wrap gap-1 lg:flex-col"
        >
          {navItems.map((item) => {
            const isActive =
              item.href === basePath
                ? pathname === item.href
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`rounded-md px-2 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "border border-[#211621] bg-[#d9ff43] text-[#211621] shadow-[2px_2px_0_#211621]"
                    : "text-[#3f2548] hover:bg-[#fffdf7]/70 hover:text-[#211621]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex flex-col gap-2">
          <BaseInput
            label="Search cards"
            type="search"
            placeholder="Search this Board"
            value={query}
            disabled={!board}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div aria-live="polite">
            {hasQuery && results.length === 0 ? (
              <p className="px-1 text-xs text-slate-500">No cards match.</p>
            ) : null}
            {results.length > 0 ? (
              <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto">
                {results.map(({ card, columnName }) => (
                  <li key={card.id}>
                    <button
                      type="button"
                      onClick={() => setOpenCardId(card.id)}
                      className="flex w-full flex-col rounded-md bg-white px-2.5 py-2 text-left shadow-2xs ring-1 ring-slate-200/80 transition-colors hover:ring-indigo-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                    >
                      <span className="text-sm font-medium break-words text-slate-900">
                        {card.title}
                      </span>
                      <span className="text-xs text-slate-500">
                        {columnName}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      </div>
    </aside>
  );
}
