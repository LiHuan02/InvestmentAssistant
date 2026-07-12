import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchIndices, fetchMarketStatus } from '../api/market';
import { isAndroidRuntime } from '../runtime';
import { useWebSocket } from './useWebSocket';
import type { IndexData } from '../types/market';

interface MarketWSMessage {
  type: string;
  data: IndexData[];
}

export function useMarketData() {
  const queryClient = useQueryClient();

  const { data, isLoading, isSuccess: indicesReady } = useQuery({
    queryKey: ['market-indices'],
    queryFn: fetchIndices,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const { data: marketStatus } = useQuery({
    queryKey: ['market-status'],
    queryFn: fetchMarketStatus,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const onWSMessage = useCallback(
    (msg: unknown) => {
      const wsMsg = msg as MarketWSMessage;
      if (wsMsg.type === 'market_update' && wsMsg.data) {
        queryClient.invalidateQueries({ queryKey: ['market-indices'] });
        queryClient.invalidateQueries({ queryKey: ['market-status'] });
      }
    },
    [queryClient]
  );

  const ws = useWebSocket<MarketWSMessage>('/ws/market', {
    onMessage: onWSMessage,
  });
  const isRealtime = !isAndroidRuntime() && ws.isConnected;

  return {
    indices: data || {},
    marketStatus: marketStatus || null,
    isLoading,
    isWSConnected: isRealtime || (isAndroidRuntime() && indicesReady),
  };
}
