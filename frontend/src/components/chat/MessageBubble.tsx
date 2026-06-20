import { useState } from 'react';
import { Typography, Space, Tag, Button, Tooltip, message } from 'antd';
import { UserOutlined, RobotOutlined, CopyOutlined, CheckOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import dayjs from 'dayjs';
import type { ChatMessage } from '../../types/chat';
import ToolCallCard from './ToolCallCard';

const { Text } = Typography;

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export default function MessageBubble({ message: msg, isStreaming }: MessageBubbleProps) {
  const isUser = msg.role === 'user';
  const hasToolCalls = msg.toolCalls && msg.toolCalls.length > 0;
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content).then(() => {
      setCopied(true);
      message.success('已复制');
      setTimeout(() => setCopied(false), 2000);
    });
  };

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Tag
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            color={isUser ? 'blue' : 'green'}
            style={{ borderRadius: '12px', margin: 0 }}
          >
            {isUser ? '我' : 'AI 助手'}
          </Tag>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {dayjs(msg.timestamp).format('HH:mm')}
          </Text>
          {!isUser && msg.content && !isStreaming && (
            <Tooltip title="复制">
              <Button
                type="text"
                size="small"
                icon={copied ? <CheckOutlined style={{ color: '#52c41a' }} /> : <CopyOutlined />}
                onClick={handleCopy}
                style={{ padding: '0 4px', height: 20 }}
              />
            </Tooltip>
          )}
        </div>
        <div
          style={{
            background: isUser ? '#e6f7ff' : '#fff',
            padding: '10px 16px',
            borderRadius: '12px',
            border: `1px solid ${isUser ? '#91d5ff' : '#e8e8e8'}`,
          }}
        >
          {hasToolCalls && (
            <div style={{ marginBottom: msg.content ? '8px' : 0 }}>
              {msg.toolCalls!.map((tc, i) => (
                <ToolCallCard key={`${tc.name}-${i}`} toolCall={tc} />
              ))}
            </div>
          )}
          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
          ) : msg.content ? (
            <div className="markdown-body" style={{ fontSize: '14px', lineHeight: 1.7 }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
            </div>
          ) : null}
          {isStreaming && !msg.content && !hasToolCalls && (
            <Text type="secondary">思考中...</Text>
          )}
          {isStreaming && msg.content && (
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
