import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchNews } from '../api/news';
import { useNewsStore } from '../store';

export function useNews() {
  const { data, isLoading } = useQuery({
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

  return {
    items: useNewsStore((s) => s.items),
    isLoading,
  };
}
