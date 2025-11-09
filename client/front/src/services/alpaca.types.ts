/**
 * Alpaca API Type Definitions
 * Comprehensive TypeScript types for all Alpaca API responses and requests
 */

// Account Types
export interface Account {
  id: string;
  account_number: string;
  status: 'ACTIVE' | 'ACCOUNT_CLOSED' | 'ACCOUNT_UPDATED' | 'ACTION_REQUIRED' | 'DISABLED' | 'INACTIVE' | 'ONBOARDING' | 'REJECTED' | 'SUBMITTED';
  crypto_status?: 'ACTIVE' | 'INACTIVE';
  currency: string;
  buying_power: string;
  regt_buying_power: string;
  daytrading_buying_power: string;
  non_marginable_buying_power: string;
  cash: string;
  accrued_fees: string;
  pending_transfer_out: string;
  pending_transfer_in: string;
  portfolio_value: string;
  pattern_day_trader: boolean;
  trading_blocked: boolean;
  transfers_blocked: boolean;
  account_blocked: boolean;
  created_at: string;
  trade_suspended_by_user: boolean;
  multiplier: string;
  shorting_enabled: boolean;
  equity: string;
  last_equity: string;
  long_market_value: string;
  short_market_value: string;
  initial_margin: string;
  maintenance_margin: string;
  last_maintenance_margin: string;
  sma: string;
  daytrade_count: number;
}

// Position Types
export interface Position {
  asset_id: string;
  symbol: string;
  exchange: string;
  asset_class: 'us_equity' | 'crypto';
  asset_marginable: boolean;
  qty: string;
  avg_entry_price: string;
  side: 'long' | 'short';
  market_value: string;
  cost_basis: string;
  unrealized_pl: string;
  unrealized_plpc: string;
  unrealized_intraday_pl: string;
  unrealized_intraday_plpc: string;
  current_price: string;
  lastday_price: string;
  change_today: string;
  qty_available: string;
}

// Order Types
export type OrderSide = 'buy' | 'sell';
export type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit' | 'trailing_stop';
export type TimeInForce = 'day' | 'gtc' | 'opg' | 'cls' | 'ioc' | 'fok';
export type OrderStatus = 
  | 'new'
  | 'partially_filled'
  | 'filled'
  | 'done_for_day'
  | 'canceled'
  | 'expired'
  | 'replaced'
  | 'pending_cancel'
  | 'pending_replace'
  | 'pending_new'
  | 'accepted'
  | 'pending'
  | 'rejected'
  | 'suspended'
  | 'calculated';

export interface Order {
  id: string;
  client_order_id: string;
  created_at: string;
  updated_at: string;
  submitted_at: string;
  filled_at: string | null;
  expired_at: string | null;
  canceled_at: string | null;
  failed_at: string | null;
  replaced_at: string | null;
  replaced_by: string | null;
  replaces: string | null;
  asset_id: string;
  symbol: string;
  asset_class: string;
  notional: string | null;
  qty: string | null;
  filled_qty: string;
  filled_avg_price: string | null;
  order_class: string;
  order_type: OrderType;
  type: OrderType;
  side: OrderSide;
  time_in_force: TimeInForce;
  limit_price: string | null;
  stop_price: string | null;
  status: OrderStatus;
  extended_hours: boolean;
  legs: Order[] | null;
  trail_percent: string | null;
  trail_price: string | null;
  hwm: string | null;
}

export interface CreateOrderRequest {
  symbol: string;
  qty?: number;
  notional?: number;
  side: OrderSide;
  type: OrderType;
  time_in_force: TimeInForce;
  limit_price?: number;
  stop_price?: number;
  trail_price?: number;
  trail_percent?: number;
  extended_hours?: boolean;
  client_order_id?: string;
  order_class?: 'simple' | 'bracket' | 'oco' | 'oto';
  take_profit?: {
    limit_price: number;
  };
  stop_loss?: {
    stop_price: number;
    limit_price?: number;
  };
}

// Asset Types
export interface Asset {
  id: string;
  class: 'us_equity' | 'crypto';
  exchange: string;
  symbol: string;
  name: string;
  status: 'active' | 'inactive';
  tradable: boolean;
  marginable: boolean;
  maintenance_margin_requirement: number;
  shortable: boolean;
  easy_to_borrow: boolean;
  fractionable: boolean;
  min_order_size?: string;
  min_trade_increment?: string;
  price_increment?: string;
}

// Watchlist Types
export interface Watchlist {
  id: string;
  account_id: string;
  created_at: string;
  updated_at: string;
  name: string;
  assets: Asset[];
}

export interface CreateWatchlistRequest {
  name: string;
  symbols: string[];
}

// Clock Types
export interface Clock {
  timestamp: string;
  is_open: boolean;
  next_open: string;
  next_close: string;
}

// Calendar Types
export interface Calendar {
  date: string;
  open: string;
  close: string;
  session_open?: string;
  session_close?: string;
}

// Portfolio History Types
export interface PortfolioHistory {
  timestamp: number[];
  equity: number[];
  profit_loss: number[];
  profit_loss_pct: number[];
  base_value: number;
  timeframe: string;
}

// Market Data Types
export interface Bar {
  t: string; // timestamp
  o: number; // open
  h: number; // high
  l: number; // low
  c: number; // close
  v: number; // volume
  n?: number; // number of trades
  vw?: number; // volume weighted average price
}

export interface Quote {
  t: string; // timestamp
  ax: string; // ask exchange
  ap: number; // ask price
  as: number; // ask size
  bx: string; // bid exchange
  bp: number; // bid price
  bs: number; // bid size
  c: string[]; // conditions
}

export interface Trade {
  t: string; // timestamp
  x: string; // exchange
  p: number; // price
  s: number; // size
  c: string[]; // conditions
  i: number; // trade id
  z: string; // tape
}

export interface Snapshot {
  symbol: string;
  latestTrade: Trade;
  latestQuote: Quote;
  minuteBar: Bar;
  dailyBar: Bar;
  prevDailyBar: Bar;
}

// News Types
export interface News {
  id: number;
  headline: string;
  author: string;
  created_at: string;
  updated_at: string;
  summary: string;
  content: string;
  url: string;
  images: Array<{
    size: string;
    url: string;
  }>;
  symbols: string[];
  source: string;
}

// Activity Types
export type ActivityType = 
  | 'FILL'
  | 'TRANS'
  | 'MISC'
  | 'ACATC'
  | 'ACATS'
  | 'CSD'
  | 'CSW'
  | 'DIV'
  | 'DIVCGL'
  | 'DIVCGS'
  | 'DIVFEE'
  | 'DIVFT'
  | 'DIVNRA'
  | 'DIVROC'
  | 'DIVTXEX'
  | 'INT'
  | 'JNLC'
  | 'JNLS'
  | 'MA'
  | 'NC'
  | 'OPASN'
  | 'OPEXP'
  | 'OPXRC'
  | 'PTC'
  | 'PTR'
  | 'REORG'
  | 'SSO'
  | 'SSP';

export interface Activity {
  id: string;
  activity_type: ActivityType;
  transaction_time: string;
  type: string;
  price?: string;
  qty?: string;
  side?: OrderSide;
  symbol?: string;
  leaves_qty?: string;
  order_id?: string;
  cum_qty?: string;
  order_status?: OrderStatus;
}

// Error Types
export interface AlpacaError {
  code: number;
  message: string;
}
