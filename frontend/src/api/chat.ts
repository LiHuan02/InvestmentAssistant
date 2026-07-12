import apiClient from './client';
import { localBackendUrl, usesLocalBackend } from '../runtime';
import type { ChatMessage, QuickCommand } from '../types/chat';

export async function fetchCommands(): Promise<QuickCommand[]> {
  const res = await apiClient.get('/chat/commands');
  return res.data;
}

interface StreamCallbacks {
  conversationId: string | null;
  onConversationId: (id: string) => void;
  onToken: (token: string) => void;
  onToolStart: (name: string, input: string) => void;
  onToolEnd: (name: string, output: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export async function sendMessageStream(
  message: string,
  history: ChatMessage[],
  callbacks: StreamCallbacks
): Promise<void> {
  const endpoint = usesLocalBackend()
    ? `${localBackendUrl}/api/v1/chat/message`
    : '/api/v1/chat/message';
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history,
      conversation_id: callbacks.conversationId,
    }),
  });

  if (!response.ok) {
    callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError('No response body');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const raw = line.slice(6).trim();
      if (raw === '[DONE]') {
        callbacks.onDone();
        return;
      }
      try {
        const parsed = JSON.parse(raw);
        if (parsed.conversation_id) {
          callbacks.onConversationId(parsed.conversation_id);
        } else if (parsed.token) {
          callbacks.onToken(parsed.token);
        } else if (parsed.tool_start) {
          callbacks.onToolStart(parsed.tool_start.name, parsed.tool_start.input);
        } else if (parsed.tool_end) {
          callbacks.onToolEnd(parsed.tool_end.name, parsed.tool_end.output);
        } else if (parsed.error) {
          callbacks.onError(parsed.error);
          return;
        }
      } catch {
        // skip malformed
      }
    }
  }
  callbacks.onDone();
}
