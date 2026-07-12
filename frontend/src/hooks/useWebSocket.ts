import { useEffect, useRef, useState, useCallback } from 'react';
import apiClient from '../api/client';
import { isAndroidRuntime, localBackendUrl, usesLocalBackend } from '../runtime';

interface UseWebSocketOptions {
  onMessage?: (data: unknown) => void;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
}

export function useWebSocket<T = unknown>(
  path: string,
  options: UseWebSocketOptions = {}
) {
  const { onMessage, reconnectInterval = 1000, maxReconnectInterval = 30000 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [isSupported, setIsSupported] = useState(!isAndroidRuntime());
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const attemptRef = useRef(0);

  const connect = useCallback(() => {
    if (!isSupported) {
      setIsConnected(false);
      return;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
    try {
      const wsUrl = usesLocalBackend()
        ? `${localBackendUrl.replace('http://', 'ws://')}${path}`
        : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${path}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        attemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as T;
          onMessage?.(data);
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (!isSupported) return;
        const delay = Math.min(
          reconnectInterval * Math.pow(2, attemptRef.current),
          maxReconnectInterval
        );
        attemptRef.current++;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      };

      wsRef.current = ws;
    } catch {
      // connection failed, will retry
    }
  }, [path, onMessage, reconnectInterval, maxReconnectInterval, isSupported]);

  useEffect(() => {
    let cancelled = false;

    const prepare = async () => {
      if (isAndroidRuntime()) {
        try {
          const res = await apiClient.get('/ws-status');
          if (!cancelled) {
            const supported = Boolean(res.data?.supported);
            setIsSupported(supported);
            if (!supported && wsRef.current) {
              wsRef.current.close();
              wsRef.current = null;
            }
          }
        } catch {
          if (!cancelled) {
            setIsSupported(false);
            setIsConnected(false);
          }
        }
      }
    };

    prepare();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { isConnected };
}
