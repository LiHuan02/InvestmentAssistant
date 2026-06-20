import axios from 'axios';

// Detect Tauri desktop environment
const isTauri = !!(window as any).__TAURI__;

// In Tauri, the frontend is served from app:// protocol,
// so we need to point to localhost for the backend API
const baseURL = isTauri ? 'http://localhost:8000/api/v1' : '/api/v1';

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});

export default apiClient;
