export interface ToolCall {
  name: string;
  input?: string;
  output?: string;
  status: 'running' | 'done';
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  toolCalls?: ToolCall[];
}

export interface QuickCommand {
  id: string;
  label: string;
  prompt: string;
  icon: string;
}
