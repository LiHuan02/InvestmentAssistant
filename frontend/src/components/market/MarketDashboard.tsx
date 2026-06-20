import { useState } from 'react';
import { Row, Col, Typography, Spin, Empty, Tag } from 'antd';
import { useMarketData } from '../../hooks/useMarketData';
import IndexCard from './IndexCard';
import ChartModal from './ChartModal';

const { Title } = Typography;

const REGION_ORDER = ['A股', '港股', '美股', '日股', '韩股', '欧洲', '大宗商品'];

export default function MarketDashboard() {
  const { indices, marketStatus, isLoading } = useMarketData();
  const [chartSymbol, setChartSymbol] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" tip="加载行情数据..." />
      </div>
    );
  }

  const regions = REGION_ORDER
    .filter((r) => indices[r] && indices[r].length > 0)
    .map((r) => [r, indices[r]] as [string, typeof indices[string]]);

  if (regions.length === 0) {
    return <Empty description="暂无行情数据" />;
  }

  return (
    <div>
      {regions.map(([region, regionIndices]) => {
        const isOpen = marketStatus?.markets?.[region] ?? true;
        return (
          <div key={region} style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Title level={5} style={{ margin: 0, color: '#666' }}>
                {region}
              </Title>
              {isOpen ? (
                <Tag color="success" style={{ fontSize: 11, lineHeight: '16px' }}>交易中</Tag>
              ) : (
                <Tag color="default" style={{ fontSize: 11, lineHeight: '16px' }}>休市</Tag>
              )}
            </div>
            <Row gutter={[12, 12]}>
              {regionIndices.map((idx) => (
                <Col xs={24} sm={12} md={8} lg={6} key={idx.symbol}>
                  <IndexCard data={idx} onClick={setChartSymbol} dimmed={!isOpen} />
                </Col>
              ))}
            </Row>
          </div>
        );
      })}
      <ChartModal
        symbol={chartSymbol}
        onClose={() => setChartSymbol(null)}
      />
    </div>
  );
}
