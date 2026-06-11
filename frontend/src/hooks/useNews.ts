import { useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchNews } from '../api/news';
import { useNewsStore } from '../store';
import { useWebSocket } from './useWebSocket';
import type { NewsItem } from '../types/news';

interface NewsWSMessage {
  type: string;
  data: NewsItem;
}

export function useNews() {
  const queryClient = useQueryClient();
  const prependItem = useNewsStore((s) => s.prependItem);

  const { data, isLoading, error } = useQuery({
    queryKey: ['news'],
    queryFn: () => fetchNews(),
    refetchInterval: 300000,
    staleTime: 60000,
  });

  useEffect(() => {
    if (data) {
      useNewsStore.setState({ items: data });
    }
  }, [data]);

  const onWSMessage = useCallback(
    (msg: unknown) => {
      const wsMsg = msg as NewsWSMessage;
      if (wsMsg.type === 'news_update' && wsMsg.data) {
        prependItem(wsMsg.data);
        queryClient.invalidateQueries({ queryKey: ['news'] });
      }
    },
    [prependItem, queryClient]
  );

  const ws = useWebSocket<NewsWSMessage>('/ws/news', {
    onMessage: onWSMessage,
  });

  return {
    items: useNewsStore((s) => s.items),
    isLoading,
    error,
    isWSConnected: ws.isConnected,
  };
}
