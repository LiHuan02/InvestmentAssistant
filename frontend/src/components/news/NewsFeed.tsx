import { Spin, Empty, List } from 'antd';
import { useNews } from '../../hooks/useNews';
import NewsCard from './NewsCard';

export default function NewsFeed() {
  const { items, isLoading } = useNews();

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" tip="加载资讯..." />
      </div>
    );
  }

  if (items.length === 0) {
    return <Empty description="暂无资讯" />;
  }

  return (
    <List
      dataSource={items}
      renderItem={(item) => <NewsCard key={item.id} item={item} />}
    />
  );
}
