import { useRef, useEffect } from 'react';
import type { ChatMessage } from '../../types/chat';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
        <div>你好！我是你的 AI 投资助手</div>
        <div style={{ fontSize: '13px', marginTop: '8px' }}>点击上方快捷指令或输入问题开始对话</div>
      </div>
    );
  }

  return (
    <div
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px 0',
        minHeight: '300px',
        maxHeight: '60vh',
      }}
    >
      {messages.map((msg, index) => (
        <MessageBubble
          key={index}
          message={msg}
          isStreaming={isStreaming && index === messages.length - 1 && msg.role === 'assistant'}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
