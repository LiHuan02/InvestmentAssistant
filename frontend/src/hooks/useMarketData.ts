import { useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchIndices } from '../api/market';
import { useMarketStore } from '../store';
import { useWebSocket } from './useWebSocket';
import type { IndexData } from '../types/market';

interface MarketWSMessage {
  type: string;
  data: IndexData[];
}

export function useMarketData() {
  const queryClient = useQueryClient();
  const setIndices = useMarketStore((s) => s.setIndices);

  const { data, isLoading, error } = useQuery({
    queryKey: ['market-indices'],
    queryFn: fetchIndices,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  useEffect(() => {
    if (data) {
      const allIndices = Object.values(data).flat();
      setIndices(allIndices);
    }
  }, [data, setIndices]);

  const onWSMessage = useCallback(
    (msg: unknown) => {
      const wsMsg = msg as MarketWSMessage;
      if (wsMsg.type === 'market_update' && wsMsg.data) {
        setIndices(wsMsg.data);
        queryClient.invalidateQueries({ queryKey: ['market-indices'] });
      }
    },
    [setIndices, queryClient]
  );

  const ws = useWebSocket<MarketWSMessage>('/ws/market', {
    onMessage: onWSMessage,
  });

  return {
    indices: data || {},
    isLoading,
    error,
    isWSConnected: ws.isConnected,
  };
}
