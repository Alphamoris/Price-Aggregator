"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useAssets } from "@/lib/use-assets";
import { AssetTable } from "@/components/asset-table";
import { Pagination } from "@/components/pagination";

type FilterType = "all" | "crypto" | "stock";

export default function DashboardPage() {
  const { isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [filter, setFilter] = useState<FilterType>("all");

  const {
    assets,
    total,
    pages,
    currentPage,
    isLoading,
    error,
    refresh,
    setPage,
  } = useAssets({
    assetType: filter === "all" ? undefined : filter,
    pageSize: 20,
    autoRefresh: true,
    refreshInterval: 30000,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Asset Aggregator
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={refresh}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Refresh
              </button>
              <button
                onClick={() => {
                  logout();
                  router.push("/login");
                }}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Market Data</h2>
              <p className="mt-1 text-sm text-gray-500">
                {total} assets • Auto-refreshes every 30 seconds
              </p>
            </div>

            <div className="flex space-x-2">
              <button
                onClick={() => setFilter("all")}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  filter === "all"
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilter("crypto")}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  filter === "crypto"
                    ? "bg-purple-600 text-white"
                    : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                }`}
              >
                Crypto
              </button>
              <button
                onClick={() => setFilter("stock")}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  filter === "stock"
                    ? "bg-green-600 text-white"
                    : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                }`}
              >
                Stocks
              </button>
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4 mb-6">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <AssetTable assets={assets} isLoading={isLoading} />
          </div>

          <Pagination
            currentPage={currentPage}
            totalPages={pages}
            onPageChange={setPage}
          />
        </div>
      </main>
    </div>
  );
}
