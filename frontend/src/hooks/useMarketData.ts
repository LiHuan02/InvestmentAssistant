import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchIndices } from '../api/market';
import { useWebSocket } from './useWebSocket';
import type { IndexData } from '../types/market';

interface MarketWSMessage {
  type: string;
  data: IndexData[];
}

export function useMarketData() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['market-indices'],
    queryFn: fetchIndices,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const onWSMessage = useCallback(
    (msg: unknown) => {
      const wsMsg = msg as MarketWSMessage;
      if (wsMsg.type === 'market_update' && wsMsg.data) {
        queryClient.invalidateQueries({ queryKey: ['market-indices'] });
      }
    },
    [queryClient]
  );

  const ws = useWebSocket<MarketWSMessage>('/ws/market', {
    onMessage: onWSMessage,
  });

  return {
    indices: data || {},
    isLoading,
    isWSConnected: ws.isConnected,
  };
}
