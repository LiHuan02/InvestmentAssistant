import { useCallback } from 'react';
import { useChatStore } from '../store';
import { sendMessageStream } from '../api/chat';
import type { ChatMessage } from '../types/chat';

export function useChat() {
  const store = useChatStore();

  const send = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      store.addMessage(userMsg);

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        toolCalls: [],
      };
      store.addMessage(assistantMsg);
      store.setStreaming(true);

      const history = store.messages.slice(0, -1).map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
      }));

      await sendMessageStream(content, history, {
        onToken: (token) => store.appendToLastAssistant(token),
        onToolStart: (name, input) => store.addToolCall(name, input),
        onToolEnd: (name, output) => store.updateToolCall(name, output),
        onDone: () => store.setStreaming(false),
        onError: (error) => {
          store.appendToLastAssistant(`\n\n**错误**: ${error}`);
          store.setStreaming(false);
        },
      });
    },
    [store]
  );

  return {
    messages: store.messages,
    isStreaming: store.isStreaming,
    send,
    clear: store.clearMessages,
  };
}
