import { Spin, Empty, List } from 'antd';
import { useNews } from '../../hooks/useNews';
import NewsCard from './NewsCard';

interface NewsFeedProps {
  limit?: number;
}

export default function NewsFeed({ limit }: NewsFeedProps) {
  const { items, isLoading } = useNews();
  const displayItems = limit ? items.slice(0, limit) : items;

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" tip="加载资讯..." />
      </div>
    );
  }

  if (displayItems.length === 0) {
    return <Empty description="暂无资讯" />;
  }

  return (
    <List
      dataSource={displayItems}
      renderItem={(item) => <NewsCard key={item.id} item={item} />}
    />
  );
}
