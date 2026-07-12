import axios from 'axios';
import { localBackendUrl, usesLocalBackend } from '../runtime';

const baseURL = usesLocalBackend() ? `${localBackendUrl}/api/v1` : '/api/v1';
export const healthURL = usesLocalBackend() ? `${localBackendUrl}/api/v1/health` : '/api/v1/health';

if (typeof window !== 'undefined') {
  console.info('[API] runtime=', usesLocalBackend() ? 'local' : 'dev-proxy', 'baseURL=', baseURL);
}

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});

export async function waitForLocalBackend(attempts = 120, delayMs = 1000): Promise<boolean> {
  if (!usesLocalBackend()) return true;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      await axios.get(healthURL, { timeout: 1000 });
      return true;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  return false;
}

export default apiClient;
