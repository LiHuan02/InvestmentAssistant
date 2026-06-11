import { Typography, Card, Switch, Divider, Space } from 'antd';
import { useSettingsStore } from '../store';

const { Title, Text } = Typography;

export default function SettingsPage() {
  const { redUp, toggleRedUp } = useSettingsStore();

  return (
    <div>
      <Title level={4}>设置</Title>
      <Card style={{ maxWidth: 600 }}>
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
