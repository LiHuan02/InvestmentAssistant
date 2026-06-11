import { Layout, Space, Typography, Badge } from 'antd';
import { WifiOutlined, DisconnectOutlined } from '@ant-design/icons';
import { useMarketData } from '../../hooks/useMarketData';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

export default function Header() {
  const { isWSConnected } = useMarketData();

  return (
    <AntHeader
      style={{
        background: '#fff',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0',
      }}
    >
      <Text strong style={{ fontSize: '18px' }}>
        市场投资助手
      </Text>
      <Space>
        {isWSConnected ? (
          <>
            <Badge count="实时" style={{ backgroundColor: '#52c41a' }} />
            <WifiOutlined style={{ color: '#52c41a' }} />
          </>
        ) : (
          <>
            <Badge count="离线" style={{ backgroundColor: '#ff4d4f' }} />
            <DisconnectOutlined style={{ color: '#ff4d4f' }} />
          </>
        )}
      </Space>
    </AntHeader>
  );
}
