export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  message: ChatMessage;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
  };
}

export interface QuickCommand {
  id: string;
  label: string;
  prompt: string;
  icon: string;
}
