import { useEffect, useState } from 'react';
import { Typography, Card, Switch, Divider, Space, InputNumber, Button, Tag, message } from 'antd';
import { useSettingsStore } from '../store';
import { getMarketSettings, updateMarketSettings } from '../api/market';
import apiClient from '../api/client';

const { Title, Text } = Typography;

interface MarketStatus {
  utc_time: string;
  any_open: boolean;
  markets: Record<string, boolean>;
}

const REGION_LABELS: Record<string, string> = {
  A股: 'A股', 港股: '港股', 美股: '美股',
  日股: '日股', 韩股: '韩股', 欧洲: '欧洲', 大宗商品: '商品',
};

export default function SettingsPage() {
  const { redUp, toggleRedUp } = useSettingsStore();
  const [marketInterval, setMarketInterval] = useState(60);
  const [newsInterval, setNewsInterval] = useState(300);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<MarketStatus | null>(null);

  useEffect(() => {
    getMarketSettings().then((s: any) => {
      if (s?.market_refresh_interval) setMarketInterval(s.market_refresh_interval);
      if (s?.news_refresh_interval) setNewsInterval(s.news_refresh_interval);
    }).catch(() => {});
    apiClient.get('/market/status').then(r => setStatus(r.data)).catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await updateMarketSettings({ market_refresh_interval: marketInterval, news_refresh_interval: newsInterval });
      message.success('设置已保存');
    } catch {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Title level={4}>设置</Title>
      <Card style={{ maxWidth: 680 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space direction="vertical" size={0}>
            <Text strong>涨跌颜色</Text>
            <Text type="secondary">中国市场：红涨绿跌；国际市场：绿涨红跌</Text>
          </Space>
          <Switch checked={redUp} onChange={toggleRedUp} checkedChildren="红涨绿跌" unCheckedChildren="绿涨红跌" />
        </div>

        <Divider />

        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong>行情刷新频率（秒）</Text>
            <div style={{ marginTop: 4 }}>
              <InputNumber min={10} max={3600} step={10} value={marketInterval} onChange={(v) => setMarketInterval(Number(v || 60))} />
            </div>
            <Text type="secondary" style={{ fontSize: 12 }}>收盘后自动停止刷新，开盘后恢复</Text>
          </div>
          <div>
            <Text strong>新闻更新频率（秒）</Text>
            <div style={{ marginTop: 4 }}>
              <InputNumber min={60} max={86400} step={60} value={newsInterval} onChange={(v) => setNewsInterval(Number(v || 300))} />
            </div>
          </div>
        </Space>

        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <Button onClick={() => { setMarketInterval(60); setNewsInterval(300); }}>重置默认</Button>
          <Button type="primary" loading={saving} onClick={save}>保存</Button>
        </div>

        <Divider />

        {status && (
          <>
            <Text strong>市场状态</Text>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {Object.entries(status.markets).map(([region, isOpen]) => (
                <Tag key={region} color={isOpen ? 'green' : 'default'}>
                  {REGION_LABELS[region] || region} {isOpen ? '交易中' : '已收盘'}
                </Tag>
              ))}
            </div>
            <Text type="secondary" style={{ fontSize: 11, marginTop: 4, display: 'block' }}>
              UTC {status.utc_time}
            </Text>
            <Divider />
          </>
        )}

        <div>
          <Text strong>颜色预览</Text>
          <Space style={{ marginTop: 8 }}>
            <span style={{ color: redUp ? '#cf1322' : '#3f8600', fontWeight: 600, fontSize: 16 }}>+1.23%</span>
            <span style={{ color: redUp ? '#3f8600' : '#cf1322', fontWeight: 600, fontSize: 16 }}>-0.85%</span>
          </Space>
        </div>

        <Divider />
        <Text type="secondary" style={{ fontSize: 12 }}>
          数据来源：新浪财经 · 腾讯财经 · 东方财富 | 仅供参考，不构成投资建议
        </Text>
      </Card>
    </div>
  );
}
