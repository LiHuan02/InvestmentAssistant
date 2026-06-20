export interface IndexData {
  symbol: string;
  name: string;
  region: string;
  price: number;
  change: number;
  change_percent: number;
  sparkline: number[];
  updated_at: string;
  unit?: string;
  alt_price?: number | null;
  alt_unit?: string;
}

export interface KlineData {
  dates: string[];
  opens: number[];
  highs: number[];
  lows: number[];
  closes: number[];
  volumes: number[];
  name: string;
}

export interface MarketStatus {
  utc_time: string;
  any_open: boolean;
  markets: Record<string, boolean>;
}
