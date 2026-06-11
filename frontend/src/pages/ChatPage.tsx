import { Typography } from 'antd';
import ChatPanel from '../components/chat/ChatPanel';

const { Title } = Typography;

export default function ChatPage() {
  return (
    <div>
      <Title level={4}>AI 投资助手</Title>
      <ChatPanel />
    </div>
  );
}
