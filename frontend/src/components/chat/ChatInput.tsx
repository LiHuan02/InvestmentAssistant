import { type RefObject } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface ChatInputProps {
  value: string;
  onSend: (message: string) => void;
  onChange: (value: string) => void;
  disabled?: boolean;
  inputRef?: RefObject<HTMLTextAreaElement | null>;
}

export default function ChatInput({ value, onSend, onChange, disabled, inputRef }: ChatInputProps) {
  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
  };

  return (
    <div style={{ display: 'flex', gap: 8, padding: '12px 0' }}>
      <TextArea
        ref={inputRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="输入问题，或输入 / 查看命令..."
        autoSize={{ minRows: 1, maxRows: 4 }}
        onPressEnter={(e) => {
          if (!e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        disabled={disabled}
        style={{ borderRadius: '8px' }}
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        style={{ height: 'auto', borderRadius: '8px' }}
      >
        发送
      </Button>
    </div>
  );
}
