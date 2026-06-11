import { useEffect, useState } from 'react';
import { Typography, Card, Switch, Divider, Space, InputNumber, Button, message } from 'antd';
import { useSettingsStore } from '../store';
import { getMarketSettings, updateMarketSettings } from '../api/market';

const { Title, Text } = Typography;

export default function SettingsPage() {
  const { redUp, toggleRedUp } = useSettingsStore();
  const [marketInterval, setMarketInterval] = useState<number>(60);
  const [newsInterval, setNewsInterval] = useState<number>(300);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMarketSettings().then((s) => {
      if (s && s.market_refresh_interval) setMarketInterval(s.market_refresh_interval);
      if (s && s.news_refresh_interval) setNewsInterval(s.news_refresh_interval);
    }).catch(() => { /* ignore */ });
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await updateMarketSettings({ market_refresh_interval: marketInterval, news_refresh_interval: newsInterval });
      message.success('设置已保存');
    } catch (e) {
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
            <Text type="secondary">中国市场惯例：红涨绿跌；国际市场惯例：绿涨红跌</Text>
          </Space>
          <Switch
            checked={redUp}
            onChange={toggleRedUp}
            checkedChildren="红涨绿跌"
            unCheckedChildren="绿涨红跌"
          />
        </div>

        <Divider />

        <div style={{ display: 'flex', gap: 24, alignItems: 'center', marginBottom: 12 }}>
          <div>
            <Text strong>实时数据更新频率（秒）</Text>
            <div>
              <InputNumber min={5} max={3600} value={marketInterval} onChange={(v) => setMarketInterval(Number(v || 60))} />
            </div>
            <Text type="secondary">控制市场行情刷新间隔，过快会被数据源限流</Text>
          </div>

          <div>
            <Text strong>新闻更新频率（秒）</Text>
            <div>
              <InputNumber min={30} max={86400} value={newsInterval} onChange={(v) => setNewsInterval(Number(v || 300))} />
            </div>
            <Text type="secondary">控制新闻拉取频率</Text>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <Button onClick={() => { getMarketSettings().then((s) => { if (s.market_refresh_interval) setMarketInterval(s.market_refresh_interval); if (s.news_refresh_interval) setNewsInterval(s.news_refresh_interval); }); }}>重置</Button>
          <Button type="primary" loading={saving} onClick={save}>保存</Button>
        </div>

        <Divider />
        <div>
          <Text strong>当前预览：</Text>
          <Space style={{ marginTop: 8 }}>
            <span style={{ color: redUp ? '#cf1322' : '#3f8600', fontWeight: 600, fontSize: 16 }}>
              +1.23%
            </span>
            <span style={{ color: redUp ? '#3f8600' : '#cf1322', fontWeight: 600, fontSize: 16 }}>
              -0.85%
            </span>
          </Space>
        </div>
        <Divider />
        <Text type="secondary" style={{ fontSize: 12 }}>
          数据来源：新浪财经、腾讯财经、Yahoo Finance | 仅供参考，不构成投资建议
        </Text>
      </Card>
    </div>
  );
}
