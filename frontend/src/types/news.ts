export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  url: string;
  published_at: string;
  related_symbols: string[];
  is_important?: boolean;
}
