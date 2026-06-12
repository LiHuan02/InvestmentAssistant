import { useState } from 'react';
import { Tag, Typography } from 'antd';
import { ToolOutlined, LoadingOutlined, CheckCircleOutlined, DownOutlined, RightOutlined } from '@ant-design/icons';
import type { ToolCall } from '../../types/chat';

const { Text, Paragraph } = Typography;

interface ToolCallCardProps {
  toolCall: ToolCall;
}

const TOOL_LABELS: Record<string, string> = {
  get_market_overview: '查询行情总览',
  get_index_detail: '查询指数详情',
  get_kline_data: '查询K线数据',
  get_latest_news: '获取最新新闻',
  get_market_status: '查询市场状态',
  tavily_search: '联网搜索',
  search_knowledge_base: '知识库检索',
};

export default function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);
  const label = TOOL_LABELS[toolCall.name] || toolCall.name;
  const isRunning = toolCall.status === 'running';

  return (
    <div
      style={{
        margin: '6px 0',
        border: '1px solid #f0f0f0',
        borderRadius: '8px',
        background: '#fafafa',
        fontSize: '12px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 10px',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        {isRunning ? (
          <LoadingOutlined style={{ color: '#1890ff' }} />
        ) : (
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
        )}
        <ToolOutlined style={{ color: '#888' }} />
        <Tag color={isRunning ? 'blue' : 'green'} style={{ margin: 0, fontSize: '11px' }}>
          {label}
        </Tag>
        <span style={{ color: '#bbb', marginLeft: 'auto' }}>
          {expanded ? <DownOutlined /> : <RightOutlined />}
        </span>
      </div>
      {expanded && (
        <div style={{ padding: '0 10px 8px 10px' }}>
          {toolCall.input && (
            <div>
              <Text type="secondary" style={{ fontSize: '11px' }}>输入</Text>
              <Paragraph
                style={{ fontSize: '11px', margin: '2px 0', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}
                ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
              >
                {toolCall.input}
              </Paragraph>
            </div>
          )}
          {toolCall.output && (
            <div>
              <Text type="secondary" style={{ fontSize: '11px' }}>输出</Text>
              <Paragraph
                style={{ fontSize: '11px', margin: '2px 0', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}
                ellipsis={{ rows: 5, expandable: true, symbol: '展开' }}
              >
                {toolCall.output}
              </Paragraph>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
