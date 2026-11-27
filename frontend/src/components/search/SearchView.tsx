"use client";

import Link from "next/link";
import { useState } from "react";
import type { FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import BaseErrorState from "@/components/shared/BaseErrorState";
import BaseInput from "@/components/shared/BaseInput";
import BaseLoadingState from "@/components/shared/BaseLoadingState";
import useSearch from "@/hooks/useSearch";

export default function SearchView() {
  const [keyword, setKeyword] = useState<string>("");
  const { results, searchedKeyword, isLoading, validationError, error, search } =
    useSearch();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void search(keyword);
  }

  return (
    <main className="rt-page">
      <div>
        <p className="rt-kicker mb-3">Find the signal</p>
        <h1 className="text-4xl font-bold text-gray-900">Search cards</h1>
      </div>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="rt-panel flex flex-col gap-3 p-5 lg:flex-row lg:items-end"
      >
        <div className="lg:max-w-md lg:flex-1">
          <BaseInput
            label="Card title keyword"
            value={keyword}
            error={validationError ?? undefined}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </div>
        <BaseButton type="submit" isLoading={isLoading}>
          Search
        </BaseButton>
      </form>

      {isLoading ? <BaseLoadingState label="Searching..." /> : null}
      {error ? (
        <BaseErrorState message={error} onRetry={() => void search(keyword)} />
      ) : null}
      {!isLoading && !error && searchedKeyword !== null ? (
        results.length === 0 ? (
          <BaseEmptyState
            message={`No Cards match "${searchedKeyword}".`}
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {results.map((result) => (
              <li
                key={result.id}
                className="rounded-xl border-[1.5px] border-[#211621] bg-[#fffdf7] p-4 shadow-[3px_3px_0_#211621] transition hover:-translate-y-0.5"
              >
                <p className="font-medium break-words text-gray-900">
                  {result.title}
                </p>
                <p className="text-sm text-gray-600">
                  <Link
                    href={`/boards/${result.board.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    {result.board.name}
                  </Link>
                  {" / "}
                  {result.column.name}
                </p>
              </li>
            ))}
          </ul>
        )
      ) : null}
    </main>
  );
}
