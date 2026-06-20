import apiClient from './client';

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
    toolCalls?: any[];
  }>;
  error?: string;
}

export async function listConversations(): Promise<Conversation[]> {
  const res = await apiClient.get('/history');
  return res.data;
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const res = await apiClient.get(`/history/${id}`);
  return res.data;
}

export async function createConversation(): Promise<Conversation> {
  const res = await apiClient.post('/history');
  return res.data;
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/history/${id}`);
}

export async function updateConversationTitle(id: string, title: string): Promise<void> {
  await apiClient.put(`/history/${id}/title`, { title });
}
