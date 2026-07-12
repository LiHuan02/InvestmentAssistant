import axios from 'axios';

// Tauri v2 does not expose __TAURI__ unless withGlobalTauri is enabled.
// Detect the actual desktop webview origin as well.
const isTauri = Boolean(
  (window as any).__TAURI__ ||
  (window as any).__TAURI_INTERNALS__ ||
  window.location.hostname === 'tauri.localhost' ||
  window.location.protocol === 'tauri:'
);

// In Tauri, the frontend is served by the app shell, so use the sidecar API.
const baseURL = isTauri ? 'http://127.0.0.1:8000/api/v1' : '/api/v1';

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});

export default apiClient;
