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

export interface MarketSummary {
  overall_sentiment: 'bullish' | 'bearish' | 'mixed' | 'neutral';
  top_gainer: IndexData | null;
  top_loser: IndexData | null;
  indices_by_region: Record<string, IndexData[]>;
  updated_at: string;
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
