import { SVGProps } from "react";

export type IconSvgProps = SVGProps<SVGSVGElement> & {
  size?: number;
};

export interface Asset {
  symbol: string;
  name: string;
  price: number;
  dailyChange: number; // percentage, e.g., 2.5 for +2.5%, -1.2 for -1.2%
  volume?: number;
  marketCap?: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: Date;
}

export interface BalanceDataPoint {
  date: Date;
  balance: number;
}

export interface StockDataPoint {
  date: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface AIMessage {
  aiId: number;
  message: string;
  timestamp: number;
}
