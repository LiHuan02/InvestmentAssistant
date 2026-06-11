import apiClient from './client';
import type { IndexData, KlineData } from '../types/market';

export async function fetchIndices(): Promise<Record<string, IndexData[]>> {
  const res = await apiClient.get('/market/indices');
  return res.data;
}

export async function fetchKline(
  symbol: string,
  period: string = 'day'
): Promise<KlineData> {
  const res = await apiClient.get(`/market/kline/${encodeURIComponent(symbol)}`, {
    params: { period },
  });
  return res.data;
}

export async function getMarketSettings(): Promise<any> {
  const res = await apiClient.get('/market/settings');
  return res.data;
}

export async function updateMarketSettings(payload: Record<string, unknown>): Promise<any> {
  const res = await apiClient.post('/market/settings', payload);
  return res.data;
}
