import { Typography } from 'antd';
import ChatPanel from '../components/chat/ChatPanel';

const { Title } = Typography;

export default function ChatPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)' }}>
      <Title level={4} style={{ marginBottom: 8, flexShrink: 0 }}>AI 投资助手</Title>
      <div style={{ flex: 1, minHeight: 0, border: '1px solid #f0f0f0', borderRadius: 8, overflow: 'hidden' }}>
        <ChatPanel />
      </div>
    </div>
  );
}
