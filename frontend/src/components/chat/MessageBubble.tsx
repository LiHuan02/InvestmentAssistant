import { Typography, Space, Tag } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../../types/chat';
import ToolCallCard from './ToolCallCard';

const { Text } = Typography;

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export default function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const hasToolCalls = message.toolCalls && message.toolCalls.length > 0;

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
          maxWidth: '85%',
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
            background: isUser ? '#e6f7ff' : '#fff',
            padding: '10px 16px',
            borderRadius: '12px',
            border: `1px solid ${isUser ? '#91d5ff' : '#e8e8e8'}`,
          }}
        >
          {hasToolCalls && (
            <div style={{ marginBottom: message.content ? '8px' : 0 }}>
              {message.toolCalls!.map((tc, i) => (
                <ToolCallCard key={`${tc.name}-${i}`} toolCall={tc} />
              ))}
            </div>
          )}
          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          ) : message.content ? (
            <div className="markdown-body" style={{ fontSize: '14px', lineHeight: 1.7 }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : null}
          {isStreaming && !message.content && !hasToolCalls && (
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
        </div>
      </Space>
    </div>
  );
}
