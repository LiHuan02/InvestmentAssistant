import { useEffect, useState } from 'react';
import { Spin, Empty, Radio, Space, Typography } from 'antd';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { fetchKline } from '../../api/market';
import type { KlineData } from '../../types/market';

const { Text } = Typography;

const PERIOD_OPTIONS = [
  { label: '分时', value: 'minute' },
  { label: '5日', value: '5day' },
  { label: '日K', value: 'day' },
  { label: '周K', value: 'week' },
];

interface ChartDetailProps {
  symbol: string;
}

export default function ChartDetail({ symbol }: ChartDetailProps) {
  const [period, setPeriod] = useState('day');
  const [data, setData] = useState<KlineData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchKline(symbol, period)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [symbol, period]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px' }}><Spin tip="加载K线数据..." /></div>;
  }

  if (!data || data.dates.length === 0) {
    return <Empty description="暂无K线数据" />;
  }

  const isKline = period === 'day' || period === 'week';
  const prevClose = data.closes.length > 1 ? data.closes[0] : data.closes[0];

  const chartData = data.dates.map((date, i) => {
    const item: Record<string, unknown> = {
      date: isKline ? date : date.slice(5, 16),
      close: data.closes[i],
    };
    if (isKline) {
      item.open = data.opens[i];
      item.high = data.highs[i];
      item.low = data.lows[i];
      item.volume = data.volumes[i];
      const isUp = data.closes[i] >= data.opens[i];
      item.isUp = isUp;
      item.barTop = isUp ? data.closes[i] : data.opens[i];
      item.barBottom = isUp ? data.opens[i] : data.closes[i];
      item.barHeight = Math.abs(data.closes[i] - data.opens[i]);
      item.wickLow = data.lows[i];
      item.wickHigh = data.highs[i];
    } else {
      item.volume = data.volumes[i] || 0;
    }
    return item;
  });

  const priceMin = Math.min(...data.lows, ...data.closes) * 0.999;
  const priceMax = Math.max(...data.highs, ...data.closes) * 1.001;
  const lastPrice = data.closes[data.closes.length - 1];
  const priceChange = lastPrice - prevClose;
  const changePercent = prevClose ? (priceChange / prevClose * 100) : 0;
  const isPositive = priceChange >= 0;
  const mainColor = isPositive ? '#3f8600' : '#cf1322';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Text strong style={{ fontSize: 18 }}>{data.name}</Text>
          <Text style={{ fontSize: 22, fontWeight: 600, color: mainColor }}>
            {lastPrice.toFixed(2)}
          </Text>
          <Text style={{ color: mainColor }}>
            {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
          </Text>
        </Space>
        <Radio.Group
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          size="small"
          options={PERIOD_OPTIONS}
          optionType="button"
        />
      </div>

      <div style={{ width: '100%', height: 400 }}>
        <ResponsiveContainer>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10 }}
              interval={Math.floor(chartData.length / 8)}
            />
            <YAxis
              domain={[priceMin, priceMax]}
              tick={{ fontSize: 10 }}
              tickFormatter={(v: number) => v.toFixed(2)}
              yAxisId="price"
            />
            <YAxis
              yAxisId="volume"
              orientation="right"
              tick={{ fontSize: 10 }}
              tickFormatter={(v: number) => v > 1e8 ? `${(v / 1e8).toFixed(0)}亿` : v > 1e4 ? `${(v / 1e4).toFixed(0)}万` : String(v)}
              domain={[0, 'auto']}
              hide
            />
            <Tooltip
              formatter={(value, name) => {
                const v = Number(value);
                if (name === 'close' || name === '收盘价' || name === '价格') return [v.toFixed(2), isKline ? '收盘价' : '价格'];
                if (name === 'high' || name === '最高') return [v.toFixed(2), '最高'];
                if (name === 'low' || name === '最低') return [v.toFixed(2), '最低'];
                if (name === 'volume' || name === '成交量') return [
                  v > 1e8 ? `${(v / 1e8).toFixed(2)}亿` : v > 1e4 ? `${(v / 1e4).toFixed(0)}万` : String(v),
                  '成交量',
                ];
                return [value, name];
              }}
            />
            {!isKline && (
              <>
                <ReferenceLine y={prevClose} stroke="#999" strokeDasharray="3 3" yAxisId="price" />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke={mainColor}
                  strokeWidth={2}
                  dot={false}
                  yAxisId="price"
                  name="价格"
                />
              </>
            )}
            {isKline && (
              <>
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke={mainColor}
                  strokeWidth={2}
                  dot={false}
                  yAxisId="price"
                  name="收盘价"
                />
                <Line
                  type="monotone"
                  dataKey="high"
                  stroke="#ff7a45"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="3 3"
                  yAxisId="price"
                  name="最高"
                />
                <Line
                  type="monotone"
                  dataKey="low"
                  stroke="#36cfc9"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="3 3"
                  yAxisId="price"
                  name="最低"
                />
              </>
            )}
            <Bar dataKey="volume" yAxisId="volume" name="成交量" fill="#d9d9d9" opacity={0.3} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
