/**
 * Alpaca API Configuration
 * Centralized configuration for Alpaca Markets API
 */

export interface AlpacaConfig {
  keyId: string;
  secretKey: string;
  paper: boolean;
  baseUrl?: string;
  dataBaseUrl?: string;
}

// Default configuration (uses environment variables)
export const getAlpacaConfig = (): AlpacaConfig => {
  return {
    keyId: import.meta.env.VITE_ALPACA_API_KEY || "",
    secretKey: import.meta.env.VITE_ALPACA_SECRET_KEY || "",
    paper: import.meta.env.VITE_ALPACA_PAPER === "true" || true,
    baseUrl: import.meta.env.VITE_ALPACA_BASE_URL,
    dataBaseUrl: import.meta.env.VITE_ALPACA_DATA_BASE_URL,
  };
};

// API Base URLs
export const ALPACA_URLS = {
  PAPER_TRADING: "https://paper-api.alpaca.markets",
  LIVE_TRADING: "https://api.alpaca.markets",
  DATA_V2: "https://data.alpaca.markets",
} as const;

export default getAlpacaConfig;
