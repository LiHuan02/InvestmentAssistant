import { Typography } from 'antd';
import NewsFeed from '../components/news/NewsFeed';

const { Title } = Typography;

export default function NewsPage() {
  return (
    <div>
      <Title level={4}>市场资讯</Title>
      <NewsFeed />
    </div>
  );
}
