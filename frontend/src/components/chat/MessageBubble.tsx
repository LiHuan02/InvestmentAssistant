import { Typography, Space, Tag } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import type { ChatMessage } from '../../types/chat';

const { Paragraph, Text } = Typography;

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export default function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '12px',
      }}
    >
      <Space
        direction="vertical"
        size={2}
        style={{
          maxWidth: '80%',
          alignItems: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        <Tag
          icon={isUser ? <UserOutlined /> : <RobotOutlined />}
          color={isUser ? 'blue' : 'green'}
          style={{ borderRadius: '12px' }}
        >
          {isUser ? '我' : 'AI 助手'}
        </Tag>
        <div
          style={{
            background: isUser ? '#e6f7ff' : '#f6ffed',
            padding: '10px 16px',
            borderRadius: '12px',
            border: `1px solid ${isUser ? '#91d5ff' : '#b7eb8f'}`,
          }}
        >
          <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {message.content}
            {isStreaming && !message.content && (
              <Text type="secondary">思考中...</Text>
            )}
            {isStreaming && message.content && (
              <span
                style={{
                  display: 'inline-block',
                  width: '6px',
                  height: '14px',
                  background: '#1890ff',
                  marginLeft: '2px',
                  animation: 'blink 1s infinite',
                }}
              />
            )}
          </Paragraph>
        </div>
      </Space>
    </div>
  );
}
