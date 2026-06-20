import { useState, useRef, useEffect } from 'react';
import { Button, Tooltip } from 'antd';
import { DeleteOutlined, MenuFoldOutlined, MenuUnfoldOutlined, ReloadOutlined } from '@ant-design/icons';
import { useChat } from '../../hooks/useChat';
import { useChatStore } from '../../store';
import QuickCommands from './QuickCommands';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ConversationSidebar from './ConversationSidebar';
import CommandPanel, { type CommandItem } from './CommandPanel';
import SlashSuggestions from './SlashSuggestions';
import apiClient from '../../api/client';

type PanelMode = 'skill' | 'mcp' | 'model' | 'temperature' | 'tokens' | 'status' | null;

export default function ChatPanel() {
  const {
    messages, isStreaming, send, clear,
    conversationId, refreshKey,
    loadConversation, newConversation,
  } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [panelMode, setPanelMode] = useState<PanelMode>(null);
  const [panelItems, setPanelItems] = useState<CommandItem[]>([]);
  const [panelTitle, setPanelTitle] = useState('');

  useEffect(() => { inputRef.current?.focus(); }, []);

  const showSlash = inputValue.startsWith('/') && inputValue.length >= 1 && !panelMode;

  // ── Panel data loaders ──────────────────────────────────────

  const openSkillPanel = async () => {
    try {
      const skills = await apiClient.get('/chat/skills').then((r) => r.data);
      setPanelItems(skills.map((s: any) => ({
        id: s.id, label: s.name, value: s.id,
        description: s.description, active: s.enabled,
      })));
      setPanelTitle('⚡ 技能管理');
      setPanelMode('skill');
    } catch { /* ignore */ }
  };

  const openMcpPanel = async () => {
    try {
      const servers = await apiClient.get('/chat/mcp').then((r) => r.data);
      setPanelItems(servers.map((s: any) => ({
        id: s.name, label: s.name, value: s.transport,
        description: s.url || s.command || '-', active: s.enabled,
      })));
      setPanelTitle('🔌 MCP 服务器');
      setPanelMode('mcp');
    } catch { /* ignore */ }
  };

  const openModelPanel = async () => {
    try {
      const data = await apiClient.get('/chat/models').then((r) => r.data);
      const currentModel = data.current;
      const models = (data.models || []).map((id: string) => ({
        id, label: id, value: id === currentModel ? '当前' : '',
        description: '', active: id === currentModel,
      }));
      if (models.length === 0) {
        // Fallback if API fails
        models.push({ id: currentModel, label: currentModel, value: '当前', description: 'API 无法获取列表', active: true });
      }
      setPanelItems(models);
      setPanelTitle(`🤖 选择模型 (${models.length} 个可用)`);
      setPanelMode('model');
    } catch { /* ignore */ }
  };

  const openTemperaturePanel = async () => {
    try {
      const config = await apiClient.get('/chat/config').then((r) => r.data);
      const current = config.temperature;
      const temps = [0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 1.0, 1.2, 1.5, 2.0].map((t) => ({
        id: String(t), label: `${t}`, value: String(t),
        description: t === 0 ? '确定性最高' : t <= 0.3 ? '较确定' : t <= 0.7 ? '平衡' : t <= 1.0 ? '较创造' : '高度创造',
        active: Math.abs(t - current) < 0.05,
      }));
      setPanelItems(temps);
      setPanelTitle('🌡️ 生成温度');
      setPanelMode('temperature');
    } catch { /* ignore */ }
  };

  const openTokensPanel = async () => {
    try {
      const config = await apiClient.get('/chat/config').then((r) => r.data);
      const current = config.max_tokens;
      const tokenOptions = [512, 1024, 2048, 4096, 8192, 16384].map((t) => ({
        id: String(t), label: `${t}`, value: `${t}`,
        description: t <= 1024 ? '简短回复' : t <= 4096 ? '中等长度' : '长回复',
        active: t === current,
      }));
      setPanelItems(tokenOptions);
      setPanelTitle('📏 最大 Token 数');
      setPanelMode('tokens');
    } catch { /* ignore */ }
  };

  const openStatusPanel = async () => {
    try {
      const [config, tools, mcp, skills] = await Promise.all([
        apiClient.get('/chat/config').then((r) => r.data),
        apiClient.get('/chat/tools').then((r) => r.data),
        apiClient.get('/chat/mcp').then((r) => r.data),
        apiClient.get('/chat/skills').then((r) => r.data),
      ]);
      const items: CommandItem[] = [
        { id: 'model', label: 'AI 模型', value: config.model, description: '' },
        { id: 'temperature', label: '温度', value: String(config.temperature), description: '' },
        { id: 'max_tokens', label: '最大Token', value: String(config.max_tokens), description: '' },
        { id: 'tools', label: '工具数', value: String(tools.length), description: tools.map((t: any) => t.name).join(', ') },
        { id: 'mcp', label: 'MCP服务器', value: String(mcp.length), description: mcp.map((s: any) => s.name).join(', ') || '无' },
        { id: 'skills', label: '已启用技能', value: String(skills.filter((s: any) => s.enabled).length), description: skills.filter((s: any) => s.enabled).map((s: any) => s.name).join(', ') || '无' },
        { id: 'tavily', label: 'Tavily 搜索', value: config.tavily_enabled ? '✅ 已启用' : '❌ 未配置', description: '' },
        { id: 'rag', label: 'RAG 知识库', value: config.rag_enabled ? '✅ 已启用' : '❌ 未配置', description: '' },
        { id: 'market_refresh', label: '行情刷新', value: `${config.market_refresh}秒`, description: '' },
        { id: 'news_refresh', label: '新闻刷新', value: `${config.news_refresh}秒`, description: '' },
      ];
      setPanelItems(items);
      setPanelTitle('📊 系统状态');
      setPanelMode('status');
    } catch { /* ignore */ }
  };

  // ── Panel toggle/select handlers ──────────────────────────

  const handleSkillToggle = async (id: string, enabled: boolean) => {
    try { await apiClient.post('/chat/skill/toggle', { id, enabled }); } catch { /* ignore */ }
  };

  const handleMcpToggle = async (_id: string, _enabled: boolean) => {
    // MCP servers are config-based, toggling triggers reload
    try { await apiClient.post('/chat/mcp/reload'); } catch { /* ignore */ }
  };

  const handleModelSelect = async (id: string) => {
    try { await apiClient.post('/chat/config', { model: id }); } catch { /* ignore */ }
  };

  const handleTemperatureSelect = async (id: string) => {
    try { await apiClient.post('/chat/config', { temperature: parseFloat(id) }); } catch { /* ignore */ }
  };

  const handleTokensSelect = async (id: string) => {
    try { await apiClient.post('/chat/config', { max_tokens: parseInt(id) }); } catch { /* ignore */ }
  };

  const closePanel = () => {
    setPanelMode(null);
    setPanelItems([]);
    setInputValue('');
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  // ── Command dispatch ──────────────────────────────────────

  const handleSend = async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;
    setInputValue('');

    if (trimmed.startsWith('/')) {
      const cmd = trimmed.split(/\s+/)[0].toLowerCase();
      const args = trimmed.slice(cmd.length).trim();

      switch (cmd) {
        case '/help': await openStatusPanel(); return;
        case '/clear': clear(); return;
        case '/new': newConversation(); return;
        case '/export': exportConversation(); return;
        case '/skill': case '/skills': await openSkillPanel(); return;
        case '/mcp': await openMcpPanel(); return;
        case '/model': await openModelPanel(); return;
        case '/temperature': await openTemperaturePanel(); return;
        case '/tokens': await openTokensPanel(); return;
        case '/status': await openStatusPanel(); return;
        case '/search':
          if (args) {
            const matches = messages.filter((m) => m.content.toLowerCase().includes(args.toLowerCase()));
            if (matches.length > 0) {
              setPanelItems(matches.slice(0, 10).map((m, i) => ({
                id: String(i), label: m.role === 'user' ? '👤 我' : '🤖 AI',
                value: '', description: m.content.length > 80 ? m.content.slice(0, 80) + '...' : m.content,
              })));
              setPanelTitle(`🔍 搜索"${args}" (${matches.length}条结果)`);
              setPanelMode('status');
            }
          }
          return;
        default: return;
      }
    }
    send(trimmed);
  };

  const handleSuggestionSelect = (cmd: string) => {
    setInputValue(cmd);
    // Auto-execute commands that don't need args
    const autoExec = ['/help', '/skill', '/mcp', '/model', '/temperature', '/tokens', '/status', '/clear', '/new'];
    if (autoExec.includes(cmd)) {
      handleSend(cmd);
    }
  };

  // ── Export ─────────────────────────────────────────────────

  const exportConversation = () => {
    if (messages.length === 0) return;
    const text = messages.map((m) => `${m.role === 'user' ? '我' : 'AI助手'}:\n${m.content}`).join('\n\n---\n\n');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `对话记录_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click(); URL.revokeObjectURL(url);
  };

  // ── Regenerate ────────────────────────────────────────────

  const handleRegenerate = () => {
    if (messages.length < 2 || isStreaming) return;
    const lastUserIdx = messages.map((m) => m.role).lastIndexOf('user');
    if (lastUserIdx < 0) return;
    const lastMsg = messages[lastUserIdx].content;
    useChatStore.getState().loadMessages(messages.slice(0, -1));
    setTimeout(() => send(lastMsg), 100);
  };

  const welcomeVisible = messages.length === 0;
  const hasAssistantMsg = messages.some((m) => m.role === 'assistant' && m.content);

  return (
    <div style={{ display: 'flex', height: '100%', gap: 0 }}>
      {sidebarOpen && (
        <ConversationSidebar
          currentId={conversationId}
          onSelect={(id) => loadConversation(id)}
          onNew={newConversation}
          refreshKey={refreshKey}
        />
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0 16px' }}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', padding: '12px 0', borderBottom: '1px solid #f0f0f0',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tooltip title={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}>
              <Button type="text" size="small"
                icon={sidebarOpen ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />}
                onClick={() => setSidebarOpen(!sidebarOpen)}
              />
            </Tooltip>
            <QuickCommands onCommand={send} />
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            {hasAssistantMsg && !isStreaming && (
              <Tooltip title="重新生成最后一条回复">
                <Button icon={<ReloadOutlined />} size="small" onClick={handleRegenerate}>重新生成</Button>
              </Tooltip>
            )}
            <Button icon={<DeleteOutlined />} size="small" onClick={clear}
              disabled={messages.length === 0 || isStreaming}>清空</Button>
          </div>
        </div>

        {/* Welcome */}
        {welcomeVisible && (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
            <div style={{ fontSize: 16, color: '#666', marginBottom: 8 }}>你好！我是你的 AI 投资助手</div>
            <div style={{ fontSize: 13, lineHeight: 2, color: '#999' }}>
              查询实时行情、分析市场走势、获取最新资讯<br />
              点击快捷指令开始，或直接输入问题<br />
              输入 <code style={{ background: '#f5f5f5', padding: '1px 4px', borderRadius: 3 }}>/</code> 查看所有命令
            </div>
          </div>
        )}

        <MessageList messages={messages} isStreaming={isStreaming} />

        {/* Interactive panels */}
        {panelMode === 'skill' && (
          <CommandPanel title={panelTitle} items={panelItems} mode="toggle"
            onToggle={handleSkillToggle} onClose={closePanel} />
        )}
        {panelMode === 'mcp' && (
          <CommandPanel title={panelTitle} items={panelItems} mode="toggle"
            onToggle={handleMcpToggle} onClose={closePanel} />
        )}
        {panelMode === 'model' && (
          <CommandPanel title={panelTitle} items={panelItems} mode="select"
            onSelect={handleModelSelect} onClose={closePanel} />
        )}
        {panelMode === 'temperature' && (
          <CommandPanel title={panelTitle} items={panelItems} mode="select"
            onSelect={handleTemperatureSelect} onClose={closePanel} />
        )}
        {panelMode === 'tokens' && (
          <CommandPanel title={panelTitle} items={panelItems} mode="select"
            onSelect={handleTokensSelect} onClose={closePanel} />
        )}
        {panelMode === 'status' && (
          <CommandPanel title={panelTitle} items={panelItems} mode="info"
            onClose={closePanel} />
        )}

        {/* Slash suggestions */}
        {showSlash && (
          <SlashSuggestions filter={inputValue} onSelect={handleSuggestionSelect} />
        )}

        <ChatInput
          onSend={handleSend} disabled={isStreaming || !!panelMode}
          onChange={(v) => setInputValue(v)}
          inputRef={inputRef}
          value={inputValue}
        />
      </div>
    </div>
  );
}
