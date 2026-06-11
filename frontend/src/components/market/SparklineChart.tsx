import { AreaChart, Area, YAxis, ResponsiveContainer } from 'recharts';

interface SparklineChartProps {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export default function SparklineChart({
  data,
  color = '#1890ff',
  width = 80,
  height = 32,
}: SparklineChartProps) {
  if (data.length < 2) return null;

  const chartData = data.map((value, index) => ({ index, value }));
  const min = Math.min(...data);
  const max = Math.max(...data);
  const padding = (max - min) * 0.1 || max * 0.001;

  return (
    <ResponsiveContainer width={width} height={height}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id={`sparkGrad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={[min - padding, max + padding]} hide />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          fill={`url(#sparkGrad-${color.replace('#', '')})`}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
