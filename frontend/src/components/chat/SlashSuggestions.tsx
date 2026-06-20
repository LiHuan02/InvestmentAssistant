interface SlashSuggestionsProps {
  filter: string;
  onSelect: (cmd: string) => void;
}

const ALL_COMMANDS = [
  { cmd: '/help', desc: '显示帮助信息' },
  { cmd: '/skill', desc: '管理技能（↑↓ Enter 切换启用）' },
  { cmd: '/mcp', desc: '管理 MCP 服务器' },
  { cmd: '/model', desc: '切换 AI 模型' },
  { cmd: '/temperature', desc: '调整生成温度' },
  { cmd: '/tokens', desc: '调整最大 Token 数' },
  { cmd: '/status', desc: '查看系统状态' },
  { cmd: '/search', desc: '搜索对话内容' },
  { cmd: '/clear', desc: '清空当前对话' },
  { cmd: '/new', desc: '开始新对话' },
  { cmd: '/export', desc: '导出对话为文本' },
];

export default function SlashSuggestions({ filter, onSelect }: SlashSuggestionsProps) {
  const query = filter.slice(1).toLowerCase();
  const matches = ALL_COMMANDS.filter((c) =>
    c.cmd.toLowerCase().includes('/' + query)
  );

  if (matches.length === 0) return null;

  return (
    <div style={{
      background: '#fff', border: '1px solid #d9d9d9', borderRadius: 8,
      padding: '4px 0', marginBottom: 4, boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      maxHeight: 240, overflow: 'auto',
    }}>
      {matches.map((c) => (
        <div
          key={c.cmd}
          onClick={() => onSelect(c.cmd)}
          style={{
            padding: '6px 12px', cursor: 'pointer', display: 'flex',
            justifyContent: 'space-between', alignItems: 'center',
            fontSize: 13, transition: 'background 0.15s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <code style={{ color: '#1890ff', fontWeight: 500 }}>{c.cmd}</code>
          <span style={{ color: '#999', fontSize: 12 }}>{c.desc}</span>
        </div>
      ))}
    </div>
  );
}
