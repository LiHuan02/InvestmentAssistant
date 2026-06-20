import { useState, useEffect, useCallback, useRef } from 'react';

export interface CommandItem {
  id: string;
  label: string;
  value: string;
  description: string;
  active?: boolean;
}

interface CommandPanelProps {
  title: string;
  items: CommandItem[];
  mode: 'toggle' | 'select' | 'info';
  onSelect?: (id: string) => void;
  onToggle?: (id: string, value: boolean) => void;
  onClose: () => void;
}

export default function CommandPanel({ title, items, mode, onSelect, onToggle, onClose }: CommandPanelProps) {
  const [cursor, setCursor] = useState(0);
  const [localItems, setLocalItems] = useState(items);
  const listRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => { setLocalItems(items); setCursor(0); }, [items]);

  // Auto-scroll focused item into view
  useEffect(() => {
    const el = itemRefs.current[cursor];
    if (el) el.scrollIntoView({ block: 'nearest' });
  }, [cursor]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (mode === 'info') {
      if (e.key === 'Escape') { e.preventDefault(); onClose(); }
      return;
    }
    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault();
        setCursor((c) => (c > 0 ? c - 1 : localItems.length - 1));
        break;
      case 'ArrowDown':
        e.preventDefault();
        setCursor((c) => (c < localItems.length - 1 ? c + 1 : 0));
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (!localItems[cursor]) break;
        if (mode === 'select') {
          onSelect?.(localItems[cursor].id);
          onClose();
        } else if (mode === 'toggle') {
          const item = localItems[cursor];
          const newActive = !item.active;
          setLocalItems(localItems.map((it, i) =>
            i === cursor ? { ...it, active: newActive } : it
          ));
          onToggle?.(item.id, newActive);
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  }, [cursor, localItems, mode, onSelect, onToggle, onClose]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [handleKeyDown]);

  const hint = mode === 'toggle'
    ? '↑↓ 导航 · Enter 切换 · Esc 退出'
    : mode === 'select'
    ? '↑↓ 导航 · Enter 选中 · Esc 退出'
    : 'Esc 退出';

  return (
    <div style={{
      background: '#1e1e1e', color: '#d4d4d4',
      fontFamily: "'Cascadia Code', 'Fira Code', Consolas, monospace",
      fontSize: 13, lineHeight: '22px', borderRadius: 8,
      padding: '12px 16px', marginBottom: 8, userSelect: 'none',
      display: 'flex', flexDirection: 'column', maxHeight: '50vh',
    }}>
      <div style={{
        borderBottom: '1px solid #444', paddingBottom: 8, marginBottom: 8,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexShrink: 0,
      }}>
        <span style={{ color: '#569cd6', fontWeight: 600 }}>{title}</span>
        <span style={{ color: '#666', fontSize: 11 }}>{hint}</span>
      </div>

      <div ref={listRef} style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', minHeight: 0 }}>
        {localItems.map((item, i) => {
          const focused = i === cursor;
          return (
            <div
              key={item.id}
              ref={(el) => { itemRefs.current[i] = el; }}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '4px 8px', borderRadius: 4,
                background: focused ? '#264f78' : 'transparent',
                cursor: mode !== 'info' ? 'pointer' : 'default',
              }}
              onClick={() => {
                if (mode === 'info') return;
                setCursor(i);
                if (mode === 'select') { onSelect?.(item.id); onClose(); }
                else if (mode === 'toggle') {
                  const newActive = !item.active;
                  setLocalItems(localItems.map((it, idx) =>
                    idx === i ? { ...it, active: newActive } : it
                  ));
                  onToggle?.(item.id, newActive);
                }
              }}
            >
              <span style={{ width: 16, color: focused ? '#dcdcaa' : 'transparent', flexShrink: 0 }}>
                {focused ? '▸' : ' '}
              </span>

              {mode === 'toggle' && (
                <span style={{
                  display: 'inline-block', width: 36, textAlign: 'center',
                  borderRadius: 3, fontSize: 11, fontWeight: 500, padding: '0 4px',
                  background: item.active ? '#2ea04370' : '#3c3c3c',
                  color: item.active ? '#4ec9b0' : '#808080', flexShrink: 0,
                }}>
                  {item.active ? '启用' : '禁用'}
                </span>
              )}

              {mode === 'select' && (
                <span style={{
                  width: 16, textAlign: 'center', color: item.active ? '#4ec9b0' : '#555',
                  flexShrink: 0, fontSize: 14,
                }}>
                  {item.active ? '●' : '○'}
                </span>
              )}

              <span style={{ color: '#9cdcfe', minWidth: 100, flexShrink: 0 }}>{item.label}</span>
              <span style={{ color: '#ce9178', minWidth: 80, flexShrink: 0 }}>{item.value}</span>
              <span style={{ color: '#808080', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.description}
              </span>
            </div>
          );
        })}
      </div>

      {mode === 'toggle' && (
        <div style={{
          borderTop: '1px solid #444', marginTop: 8, paddingTop: 6,
          display: 'flex', justifyContent: 'space-between', color: '#666', fontSize: 11,
          flexShrink: 0,
        }}>
          <span>{localItems.filter((i) => i.active).length}/{localItems.length} 已启用</span>
          <span>Esc 退出</span>
        </div>
      )}
    </div>
  );
}
