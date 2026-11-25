"use client";

import { useCallback, useState } from "react";
import useToast from "@/hooks/useToast";
import { apiClient } from "@/lib/apiClient";
import { getErrorMessage } from "@/lib/errorHandler";
import { validateSearchKeyword } from "@/lib/search";
import type { SearchResult } from "@/types/api";

interface UseSearchResult {
  results: SearchResult[];
  searchedKeyword: string | null;
  isLoading: boolean;
  validationError: string | null;
  error: string | null;
  search: (keyword: string) => Promise<void>;
}

export default function useSearch(): UseSearchResult {
  const { showError } = useToast();
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searchedKeyword, setSearchedKeyword] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (keyword: string) => {
    const problem = validateSearchKeyword(keyword);
    setValidationError(problem);
    if (problem) return;
    const trimmed = keyword.trim();
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.searchCards(trimmed);
      setResults(response.items);
      setSearchedKeyword(trimmed);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Search failed."));
      showError(err, "Search failed.");
    } finally {
      setIsLoading(false);
    }
  }, [showError]);

  return {
    results,
    searchedKeyword,
    isLoading,
    validationError,
    error,
    search,
  };
}
