import apiClient from './client';
import type { ChatMessage, QuickCommand } from '../types/chat';

export async function fetchCommands(): Promise<QuickCommand[]> {
  const res = await apiClient.get('/chat/commands');
  return res.data;
}

export async function fetchHistory(): Promise<ChatMessage[]> {
  const res = await apiClient.get('/chat/history');
  return res.data;
}

export async function clearHistory(): Promise<void> {
  await apiClient.delete('/chat/history');
}

export async function sendMessageStream(
  message: string,
  history: ChatMessage[],
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  const response = await fetch('/api/v1/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });

  if (!response.ok) {
    onError(`HTTP ${response.status}: ${response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError('No response body');
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
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim();
        if (data === '[DONE]') {
          onDone();
          return;
        }
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            onError(parsed.error);
            return;
          }
          if (parsed.token) {
            onToken(parsed.token);
          }
        } catch {
          // skip malformed chunks
        }
      }
    }
  }
  onDone();
}
