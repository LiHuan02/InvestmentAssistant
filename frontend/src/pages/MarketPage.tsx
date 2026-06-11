import { Typography } from 'antd';
import MarketDashboard from '../components/market/MarketDashboard';

const { Title } = Typography;

export default function MarketPage() {
  return (
    <div>
      <Title level={4}>全球行情</Title>
      <MarketDashboard />
    </div>
  );
}
