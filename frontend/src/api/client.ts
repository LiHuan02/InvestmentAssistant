import axios from 'axios';
import { localBackendUrl, usesLocalBackend } from '../runtime';

const baseURL = usesLocalBackend() ? `${localBackendUrl}/api/v1` : '/api/v1';

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});

export default apiClient;
