import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/layout/AppLayout';
import MarketPage from './pages/MarketPage';
import NewsPage from './pages/NewsPage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import SetupWizard from './components/SetupWizard';
import { getAppSettings } from './api/settings';
import 'dayjs/locale/zh-cn';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function AppContent() {
  const [ready, setReady] = useState(false);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSetup();
  }, []);

  const checkSetup = async () => {
    try {
      const s = await getAppSettings();
      if (s.configured) {
        localStorage.setItem('setup_complete', 'true');
        setReady(true);
      } else {
        setNeedsSetup(true);
      }
    } catch {
      // Keep the setup wizard for a real backend connection failure.
      setNeedsSetup(true);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (needsSetup && !ready) {
    return <SetupWizard onComplete={() => { setNeedsSetup(false); setReady(true); }} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<MarketPage />} />
          <Route path="market" element={<Navigate to="/" replace />} />
          <Route path="news" element={<NewsPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#1890ff', borderRadius: 6 } }}>
        <AppContent />
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
