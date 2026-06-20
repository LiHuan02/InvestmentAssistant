import apiClient from './client';

export interface AppSettings {
  ai_api_key: string;
  ai_base_url: string;
  ai_model: string;
  ai_provider: string;
  tavily_api_key: string;
  twelvedata_api: string;
  rag_persist_dir: string;
  market_refresh_interval: number;
  news_refresh_interval: number;
  configured: boolean;
}

export interface SettingsUpdate {
  ai_api_key?: string;
  ai_base_url?: string;
  ai_model?: string;
  tavily_api_key?: string;
  twelvedata_api?: string;
  rag_persist_dir?: string;
  market_refresh_interval?: number;
  news_refresh_interval?: number;
}

export interface TestResult {
  ok: boolean;
  message: string;
  response?: string;
}

export async function getAppSettings(): Promise<AppSettings> {
  const res = await apiClient.get('/settings');
  return res.data;
}

export async function updateAppSettings(payload: SettingsUpdate): Promise<{ updated: string[] }> {
  const res = await apiClient.post('/settings', payload);
  return res.data;
}

export async function testConnection(
  apiKey: string,
  baseUrl: string,
  model: string
): Promise<TestResult> {
  const res = await apiClient.post('/settings/test-connection', {
    api_key: apiKey,
    base_url: baseUrl,
    model,
  });
  return res.data;
}
