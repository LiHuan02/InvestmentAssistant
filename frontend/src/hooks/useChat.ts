import { useCallback, useState } from 'react';
import { useChatStore } from '../store';
import { sendMessageStream } from '../api/chat';
import { getConversation } from '../api/history';
import type { ChatMessage, ToolCall } from '../types/chat';

export function useChat() {
  const store = useChatStore();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await getConversation(id);
      if (conv.error) return;
      const msgs: ChatMessage[] = conv.messages.map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: m.timestamp,
        toolCalls: m.toolCalls as ToolCall[] | undefined,
      }));
      store.loadMessages(msgs);
      setConversationId(id);
    } catch { /* ignore */ }
  }, [store]);

  const newConversation = useCallback(() => {
    store.clearMessages();
    setConversationId(null);
  }, [store]);

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
        conversationId,
        onConversationId: (id) => {
          setConversationId(id);
          setRefreshKey((k) => k + 1);
        },
        onToken: (token) => store.appendToLastAssistant(token),
        onToolStart: (name, input) => store.addToolCall(name, input),
        onToolEnd: (name, output) => store.updateToolCall(name, output),
        onDone: () => {
          store.setStreaming(false);
          setRefreshKey((k) => k + 1);
        },
        onError: (error) => {
          store.appendToLastAssistant(`\n\n**错误**: ${error}`);
          store.setStreaming(false);
        },
      });
    },
    [store, conversationId]
  );

  return {
    messages: store.messages,
    isStreaming: store.isStreaming,
    conversationId,
    refreshKey,
    send,
    loadConversation,
    newConversation,
    clear: () => { store.clearMessages(); setConversationId(null); },
  };
}
