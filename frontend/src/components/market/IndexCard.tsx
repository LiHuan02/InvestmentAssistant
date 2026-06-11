import { useState } from 'react';
import { Card, Statistic, Space, Tooltip } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, SwapOutlined } from '@ant-design/icons';
import type { IndexData } from '../../types/market';
import { useColor } from '../../store';
import SparklineChart from './SparklineChart';

interface IndexCardProps {
  data: IndexData;
  onClick?: (symbol: string) => void;
}

export default function IndexCard({ data, onClick }: IndexCardProps) {
  const { getColor } = useColor();
  const [showAlt, setShowAlt] = useState(false);
  const isPositive = data.change >= 0;
  const color = getColor(data.change);
  const hasAlt = data.alt_price != null && data.alt_unit;

  const displayPrice = showAlt && hasAlt ? data.alt_price! : data.price;
  const displayUnit = showAlt && hasAlt ? data.alt_unit : (data.unit || '');

  return (
    <Tooltip title="点击查看K线图">
      <Card
        size="small"
        hoverable
        style={{ borderRadius: '8px', cursor: 'pointer' }}
        styles={{ body: { padding: '12px 16px' } }}
        onClick={(e) => {
          if ((e.target as HTMLElement).closest('.unit-toggle')) return;
          onClick?.(data.symbol);
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>
              {data.name}
            </div>
            <Statistic
              value={displayPrice}
              precision={2}
              valueStyle={{ fontSize: '20px', fontWeight: 600 }}
            />
            <Space size={4} style={{ marginTop: '4px' }}>
              <span style={{ color, fontSize: '13px' }}>
                {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                {' '}
                {Math.abs(data.change).toFixed(2)}
              </span>
              <span
                style={{
                  color: '#fff',
                  background: color,
                  padding: '1px 6px',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}
              >
                {isPositive ? '+' : ''}{data.change_percent.toFixed(2)}%
              </span>
              {displayUnit && (
                <span style={{ fontSize: '11px', color: '#999' }}>{displayUnit}</span>
              )}
              {hasAlt && (
                <span
                  className="unit-toggle"
                  style={{ cursor: 'pointer', fontSize: '11px', color: '#1890ff' }}
                  onClick={(e) => { e.stopPropagation(); setShowAlt(!showAlt); }}
                >
                  <SwapOutlined /> {showAlt ? data.unit : data.alt_unit}
                </span>
              )}
            </Space>
          </div>
          <SparklineChart data={data.sparkline} color={color} width={80} height={40} />
        </div>
      </Card>
    </Tooltip>
  );
}
