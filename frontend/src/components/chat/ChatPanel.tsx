import { Button } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useChat } from '../../hooks/useChat';
import QuickCommands from './QuickCommands';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export default function ChatPanel() {
  const { messages, isStreaming, send, clear } = useChat();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <QuickCommands onCommand={send} />
        <Button
          icon={<DeleteOutlined />}
          size="small"
          onClick={clear}
          disabled={messages.length === 0 || isStreaming}
        >
          清空
        </Button>
      </div>
      <MessageList messages={messages} isStreaming={isStreaming} />
      <ChatInput onSend={send} disabled={isStreaming} />
    </div>
  );
}
