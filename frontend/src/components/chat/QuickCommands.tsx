import { useEffect, useState } from 'react';
import { Tag, Space } from 'antd';
import { fetchCommands } from '../../api/chat';
import type { QuickCommand } from '../../types/chat';

interface QuickCommandsProps {
  onCommand: (prompt: string) => void;
}

export default function QuickCommands({ onCommand }: QuickCommandsProps) {
  const [commands, setCommands] = useState<QuickCommand[]>([]);

  useEffect(() => {
    fetchCommands().then(setCommands).catch(() => {});
  }, []);

  return (
    <Space wrap>
      {commands.map((cmd) => (
        <Tag
          key={cmd.id}
          color="blue"
          style={{
            cursor: 'pointer',
            padding: '4px 12px',
            fontSize: '13px',
            borderRadius: '12px',
          }}
          onClick={() => onCommand(cmd.prompt)}
        >
          {cmd.label}
        </Tag>
      ))}
    </Space>
  );
}
