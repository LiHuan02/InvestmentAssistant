import { useEffect, useState } from 'react';
import { List, Typography, Button, Popconfirm, Empty, Input } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  MessageOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import type { Conversation } from '../../api/history';
import { listConversations, deleteConversation } from '../../api/history';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { Text } = Typography;

interface ConversationSidebarProps {
  currentId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  refreshKey: number;
}

export default function ConversationSidebar({
  currentId,
  onSelect,
  onNew,
  refreshKey,
}: ConversationSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const data = await listConversations();
      setConversations(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [refreshKey]);

  const handleDelete = async (id: string) => {
    await deleteConversation(id);
    load();
  };

  const filtered = search
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(search.toLowerCase()))
    : conversations;

  return (
    <div style={{
      width: 240,
      borderRight: '1px solid #f0f0f0',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: '#fafafa',
    }}>
      <div style={{ padding: '12px', borderBottom: '1px solid #f0f0f0' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={onNew}
          style={{ marginBottom: 8 }}
        >
          新对话
        </Button>
        <Input
          placeholder="搜索对话..."
          prefix={<SearchOutlined style={{ color: '#bbb' }} />}
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
        {filtered.length === 0 && !loading && (
          <Empty
            description={search ? '未找到匹配的对话' : '暂无对话记录'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: 40 }}
          />
        )}
        <List
          loading={loading}
          dataSource={filtered}
          renderItem={(conv) => (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              style={{
                padding: '8px 10px',
                marginBottom: 4,
                borderRadius: 6,
                cursor: 'pointer',
                background: conv.id === currentId ? '#e6f7ff' : 'transparent',
                border: conv.id === currentId ? '1px solid #91d5ff' : '1px solid transparent',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <MessageOutlined style={{ color: '#888', fontSize: 12 }} />
                    <Text
                      ellipsis
                      strong={conv.id === currentId}
                      style={{ fontSize: 13 }}
                    >
                      {conv.title}
                    </Text>
                  </div>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {dayjs(conv.updated_at).fromNow()}
                  </Text>
                </div>
                <Popconfirm
                  title="确认删除？"
                  onConfirm={(e) => { e?.stopPropagation(); handleDelete(conv.id); }}
                  onCancel={(e) => e?.stopPropagation()}
                  okText="删除"
                  cancelText="取消"
                >
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                    style={{ flexShrink: 0 }}
                  />
                </Popconfirm>
              </div>
            </div>
          )}
        />
      </div>
    </div>
  );
}
