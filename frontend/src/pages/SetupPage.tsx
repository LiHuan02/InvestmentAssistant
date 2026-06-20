import { useState, useEffect } from 'react';
import { getAppSettings, type AppSettings } from '../api/settings';
import SetupWizard from '../components/SetupWizard';
import { Spin } from 'antd';

interface SetupPageProps {
  onReady: () => void;
}

export default function SetupPage({ onReady }: SetupPageProps) {
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  useEffect(() => {
    checkSetup();
  }, []);

  const checkSetup = async () => {
    try {
      // Check localStorage first
      if (localStorage.getItem('setup_complete') === 'true') {
        onReady();
        return;
      }
      // Check backend config
      const settings: AppSettings = await getAppSettings();
      if (settings.configured) {
        localStorage.setItem('setup_complete', 'true');
        onReady();
      } else {
        setNeedsSetup(true);
      }
    } catch {
      setNeedsSetup(true);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Spin size="large" tip="检查配置..." />
      </div>
    );
  }

  if (needsSetup) {
    return <SetupWizard onComplete={onReady} />;
  }

  return null;
}
