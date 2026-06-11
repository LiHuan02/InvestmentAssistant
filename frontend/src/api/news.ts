import apiClient from './client';
import type { NewsItem } from '../types/news';

export async function fetchNews(
  limit: number = 20,
  offset: number = 0
): Promise<NewsItem[]> {
  const res = await apiClient.get('/news', { params: { limit, offset } });
  return res.data;
}
