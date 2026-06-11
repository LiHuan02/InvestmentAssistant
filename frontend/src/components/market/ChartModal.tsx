import { Modal } from 'antd';
import ChartDetail from './ChartDetail';

interface ChartModalProps {
  symbol: string | null;
  onClose: () => void;
}

export default function ChartModal({ symbol, onClose }: ChartModalProps) {
  if (!symbol) return null;

  return (
    <Modal
      open={!!symbol}
      onCancel={onClose}
      footer={null}
      width={900}
      destroyOnClose
      title={null}
      styles={{ body: { paddingTop: 24 } }}
    >
      {symbol && <ChartDetail symbol={symbol} />}
    </Modal>
  );
}
