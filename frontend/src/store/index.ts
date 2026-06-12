import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { NewsItem } from '../types/news';
import type { ChatMessage } from '../types/chat';

interface SettingsStore {
  redUp: boolean;
  toggleRedUp: () => void;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      redUp: true,
      toggleRedUp: () => set((s) => ({ redUp: !s.redUp })),
    }),
    { name: 'app-settings' }
  )
);

export function useColor() {
  const redUp = useSettingsStore((s) => s.redUp);
  return {
    upColor: redUp ? '#cf1322' : '#3f8600',
    downColor: redUp ? '#3f8600' : '#cf1322',
    getColor: (change: number) => (change >= 0 ? (redUp ? '#cf1322' : '#3f8600') : (redUp ? '#3f8600' : '#cf1322')),
  };
}

interface NewsStore {
  items: NewsItem[];
  prependItem: (item: NewsItem) => void;
}

export const useNewsStore = create<NewsStore>((set) => ({
  items: [],
  prependItem: (item) =>
    set((state) => {
      if (state.items.some((i) => i.id === item.id)) return state;
      return { items: [item, ...state.items] };
    }),
}));

interface ChatStore {
  messages: ChatMessage[];
  isStreaming: boolean;
  addMessage: (msg: ChatMessage) => void;
  appendToLastAssistant: (token: string) => void;
  addToolCall: (name: string, input: string) => void;
  updateToolCall: (name: string, output: string) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  appendToLastAssistant: (token) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === 'assistant') {
        messages[messages.length - 1] = { ...last, content: last.content + token };
      }
      return { messages };
    }),
  addToolCall: (name, input) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === 'assistant') {
        const toolCalls = [...(last.toolCalls || []), { name, input, status: 'running' as const }];
        messages[messages.length - 1] = { ...last, toolCalls };
      }
      return { messages };
    }),
  updateToolCall: (name, output) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === 'assistant' && last.toolCalls) {
        const toolCalls = last.toolCalls.map((tc) =>
          tc.name === name && tc.status === 'running'
            ? { ...tc, output, status: 'done' as const }
            : tc
        );
        messages[messages.length - 1] = { ...last, toolCalls };
      }
      return { messages };
    }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  clearMessages: () => set({ messages: [], isStreaming: false }),
}));
