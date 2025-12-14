"use client";

import { useState, useEffect, useCallback } from "react";
import { Asset, AssetListResponse, api } from "@/lib/api";

interface UseAssetsOptions {
  assetType?: "crypto" | "stock";
  page?: number;
  pageSize?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseAssetsReturn {
  assets: Asset[];
  total: number;
  pages: number;
  currentPage: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
  setPage: (page: number) => void;
}

export function useAssets({
  assetType,
  page = 1,
  pageSize = 20,
  autoRefresh = true,
  refreshInterval = 30000,
}: UseAssetsOptions = {}): UseAssetsReturn {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(page);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevAssetType, setPrevAssetType] = useState(assetType);

  if (assetType !== prevAssetType) {
    setPrevAssetType(assetType);
    setCurrentPage(1);
  }

  const fetchAssets = useCallback(async () => {
    try {
      setError(null);
      let response: AssetListResponse;

      if (assetType === "crypto") {
        response = await api.getCryptos(currentPage, pageSize);
      } else if (assetType === "stock") {
        response = await api.getStocks(currentPage, pageSize);
      } else {
        response = await api.getAssets(currentPage, pageSize);
      }

      setAssets(response.items);
      setTotal(response.total);
      setPages(response.pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch assets");
    } finally {
      setIsLoading(false);
    }
  }, [assetType, currentPage, pageSize]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchAssets, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAssets]);

  const refresh = useCallback(() => {
    setIsLoading(true);
    fetchAssets();
  }, [fetchAssets]);

  const setPage = useCallback((newPage: number) => {
    setCurrentPage(newPage);
  }, []);

  return {
    assets,
    total,
    pages,
    currentPage,
    isLoading,
    error,
    refresh,
    setPage,
  };
}
