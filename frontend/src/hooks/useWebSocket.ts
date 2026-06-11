import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  onMessage?: (data: unknown) => void;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
}

interface UseWebSocketResult {
  isConnected: boolean;
  error: Error | null;
  lastMessage: unknown;
}

export function useWebSocket<T = unknown>(
  path: string,
  options: UseWebSocketOptions = {}
): UseWebSocketResult {
  const { onMessage, reconnectInterval = 1000, maxReconnectInterval = 30000 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastMessage, setLastMessage] = useState<unknown>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const attemptRef = useRef(0);

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const ws = new WebSocket(`${protocol}//${host}${path}`);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        attemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as T;
          setLastMessage(data);
          onMessage?.(data);
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = () => {
        setError(new Error('WebSocket error'));
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
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Connection failed'));
    }
  }, [path, onMessage, reconnectInterval, maxReconnectInterval]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { isConnected, error, lastMessage };
}
