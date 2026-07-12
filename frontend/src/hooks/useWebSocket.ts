import { useEffect, useRef, useState, useCallback } from 'react';

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
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const attemptRef = useRef(0);

  const connect = useCallback(() => {
    try {
      const isTauri = Boolean(
        (window as any).__TAURI__ ||
        (window as any).__TAURI_INTERNALS__ ||
        window.location.hostname === 'tauri.localhost' ||
        window.location.protocol === 'tauri:'
      );
      const wsUrl = isTauri
        ? `ws://127.0.0.1:8000${path}`
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
  }, [path, onMessage, reconnectInterval, maxReconnectInterval]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { isConnected };
}
