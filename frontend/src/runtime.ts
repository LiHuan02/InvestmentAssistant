import { Capacitor } from '@capacitor/core';

export function isTauriRuntime(): boolean {
  return Boolean(
    (window as any).__TAURI__ ||
    (window as any).__TAURI_INTERNALS__ ||
    window.location.hostname === 'tauri.localhost' ||
    window.location.protocol === 'tauri:'
  );
}

export function isAndroidRuntime(): boolean {
  return Capacitor.getPlatform() === 'android';
}

export function usesLocalBackend(): boolean {
  return isTauriRuntime() || isAndroidRuntime();
}

export const localBackendUrl = 'http://127.0.0.1:8000';
