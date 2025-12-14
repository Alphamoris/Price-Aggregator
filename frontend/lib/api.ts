const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiError {
  error: string;
  details?: Record<string, unknown>;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_type: "crypto" | "stock";
  price_usd: string | null;
  change_24h: string | null;
  market_cap: string | null;
  volume_24h: string | null;
  source: "coingecko" | "alphavantage";
  fetched_at: string;
  created_at: string;
  updated_at: string;
}

export interface AssetListResponse {
  items: Asset[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("token", token);
      } else {
        localStorage.removeItem("token");
      }
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("token");
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        error: "Request failed",
      }));
      throw new Error(error.error || "Request failed");
    }

    return response.json();
  }

  async register(
    username: string,
    email: string,
    password: string
  ): Promise<User> {
    return this.request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
  }

  async login(username: string, password: string): Promise<Token> {
    const response = await this.request<Token>("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  logout() {
    this.setToken(null);
  }

  async getAssets(
    page: number = 1,
    pageSize: number = 20,
    assetType?: "crypto" | "stock"
  ): Promise<AssetListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (assetType) {
      params.append("asset_type", assetType);
    }
    return this.request<AssetListResponse>(
      `/api/v1/assets?${params.toString()}`
    );
  }

  async getCryptos(
    page: number = 1,
    pageSize: number = 20
  ): Promise<AssetListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    return this.request<AssetListResponse>(
      `/api/v1/assets/crypto?${params.toString()}`
    );
  }

  async getStocks(
    page: number = 1,
    pageSize: number = 20
  ): Promise<AssetListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    return this.request<AssetListResponse>(
      `/api/v1/assets/stocks?${params.toString()}`
    );
  }

  async getAssetBySymbol(symbol: string): Promise<Asset> {
    return this.request<Asset>(`/api/v1/assets/${symbol}`);
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/api/v1/health");
  }
}

export const api = new ApiClient(API_URL);
