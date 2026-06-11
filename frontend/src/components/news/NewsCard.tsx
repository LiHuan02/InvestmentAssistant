import { Card, Typography, Tag } from 'antd';
import { FireOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { NewsItem } from '../../types/news';

const { Text, Paragraph } = Typography;

interface NewsCardProps {
  item: NewsItem;
}

export default function NewsCard({ item }: NewsCardProps) {
  const isImportant = item.is_important;

  return (
    <Card
      size="small"
      hoverable
      style={{
        marginBottom: '8px',
        borderRadius: '8px',
        borderLeft: isImportant ? '3px solid #ff4d4f' : undefined,
        background: isImportant ? '#fff2f0' : undefined,
      }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
        {isImportant && (
          <Tag color="red" icon={<FireOutlined />} style={{ flexShrink: 0, marginTop: '2px' }}>
            重要
          </Tag>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: 'block' }}
          >
            <Text
              strong={isImportant}
              style={{
                fontSize: '14px',
                display: 'block',
                marginBottom: '4px',
                color: isImportant ? '#cf1322' : undefined,
              }}
            >
              {item.title}
            </Text>
          </a>
          <Paragraph
            type="secondary"
            ellipsis={{ rows: 2 }}
            style={{ marginBottom: '8px', fontSize: '13px' }}
          >
            {item.summary}
          </Paragraph>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag color="blue">{item.source}</Tag>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {dayjs(item.published_at).format('M月D日 HH:mm')}
            </Text>
            {item.related_symbols.map((sym) => (
              <Tag key={sym} color="green" style={{ fontSize: '11px' }}>
                {sym}
              </Tag>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
