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
    <main className="flex flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold text-gray-900">Search Cards</h1>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="flex flex-col gap-2 lg:flex-row lg:items-end"
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
                className="rounded-md border border-gray-200 bg-white p-3"
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
