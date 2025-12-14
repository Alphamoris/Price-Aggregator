"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex justify-between items-center py-6">
          <div className="text-2xl font-bold text-gray-900">
            Asset Aggregator
          </div>
          <div className="space-x-4">
            <Link
              href="/login"
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700"
            >
              Get Started
            </Link>
          </div>
        </nav>

        <main className="flex flex-col items-center justify-center min-h-[80vh] text-center">
          <h1 className="text-5xl font-extrabold text-gray-900 mb-6">
            Crypto & Stock Market
            <br />
            <span className="text-blue-600">Data Aggregator</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mb-8">
            Real-time market data from CoinGecko and Alpha Vantage. Track
            cryptocurrencies and stocks in one unified dashboard.
          </p>
          <div className="flex space-x-4">
            <Link
              href="/register"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium text-lg hover:bg-blue-700 transition-colors"
            >
              Create Free Account
            </Link>
            <Link
              href="/login"
              className="bg-white text-gray-700 px-6 py-3 rounded-lg font-medium text-lg border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Sign In
            </Link>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl">
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">📈</div>
              <h3 className="font-bold text-lg mb-2">Real-time Data</h3>
              <p className="text-gray-600">
                Prices update automatically every 30 seconds
              </p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">🔒</div>
              <h3 className="font-bold text-lg mb-2">Secure Auth</h3>
              <p className="text-gray-600">
                JWT-based authentication with bcrypt password hashing
              </p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">⚡</div>
              <h3 className="font-bold text-lg mb-2">Fast & Cached</h3>
              <p className="text-gray-600">
                In-memory caching for lightning-fast responses
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
