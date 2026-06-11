export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface QuickCommand {
  id: string;
  label: string;
  prompt: string;
  icon: string;
}
