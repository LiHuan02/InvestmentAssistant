import { useState } from 'react';
import { Button, Input, Steps, Typography, Card, Space, Alert, Radio, message } from 'antd';
import {
  ApiOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import apiClient from '../api/client';
import { testConnection, updateAppSettings } from '../api/settings';
import { isTauriRuntime, isAndroidRuntime } from '../runtime';

const { Title, Text, Paragraph } = Typography;

const PROVIDERS = [
  {
    key: 'ollama_cloud',
    label: 'Ollama Cloud',
    baseUrl: 'https://ollama.com/v1',
    model: 'glm-4.7',
    desc: '免费模型：GLM、MiniMax、DeepSeek、Kimi 等',
  },
  {
    key: 'ollama_local',
    label: 'Ollama 本地',
    baseUrl: 'http://localhost:11434/v1',
    model: 'qwen2.5:7b',
    desc: '本地运行，无需联网，完全免费',
  },
  {
    key: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    desc: 'GPT-4o / GPT-4o-mini，需付费',
  },
  {
    key: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    desc: '高性价比，有免费额度',
  },
  {
    key: 'custom',
    label: '自定义',
    baseUrl: '',
    model: '',
    desc: '任何 OpenAI 兼容接口',
  },
];

interface SetupWizardProps {
  onComplete: () => void;
}

export default function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState(0);
  const [provider, setProvider] = useState(PROVIDERS[0]);
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState(PROVIDERS[0].baseUrl);
  const [model, setModel] = useState(PROVIDERS[0].model);
  const [tavilyKey, setTavilyKey] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const handleProviderChange = (key: string) => {
    const p = PROVIDERS.find((pr) => pr.key === key)!;
    setProvider(p);
    setBaseUrl(p.baseUrl);
    setModel(p.model);
    setTestResult(null);
  };

  const waitForBackend = async (attempts = 90): Promise<boolean> => {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        await apiClient.get('/health', { timeout: 1000 });
        return true;
      } catch {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
    return false;
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      if (isTauriRuntime() || isAndroidRuntime()) {
        const backendReady = await waitForBackend();
        if (!backendReady) {
          setTestResult({ ok: false, message: '本地后端尚未启动，请稍后重试。' });
          return;
        }
      }
      const result = await testConnection(apiKey, baseUrl, model);
      setTestResult(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : '未知网络错误';
      setTestResult({ ok: false, message: `请求本地后端失败：${message}` });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (isTauriRuntime() || isAndroidRuntime()) {
        const backendReady = await waitForBackend();
        if (!backendReady) {
          message.error('本地后端尚未启动，请稍后重试');
          return;
        }
      }
      await updateAppSettings({
        ai_api_key: apiKey,
        ai_base_url: baseUrl,
        ai_model: model,
        tavily_api_key: tavilyKey || undefined,
      });
      localStorage.setItem('setup_complete', 'true');
      message.success('配置已保存！');
      onComplete();
    } catch (error) {
      const detail = error instanceof Error ? error.message : '未知网络错误';
      message.error(`保存失败：${detail}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      minHeight: '100vh', background: '#f5f5f5', padding: 24,
    }}>
      <Card style={{ maxWidth: 640, width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3} style={{ marginBottom: 4 }}>📊 市场投资助手</Title>
          <Text type="secondary">首次使用，请配置 AI 服务</Text>
        </div>

        <Steps
          current={step}
          size="small"
          style={{ marginBottom: 32 }}
          items={[
            { title: '选择提供商' },
            { title: '填写配置' },
            { title: '测试连接' },
            { title: '完成' },
          ]}
        />

        {/* Step 0: 选择提供商 */}
        {step === 0 && (
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            <Paragraph>选择一个 AI 服务提供商。所有兼容 OpenAI 接口的服务均可使用。</Paragraph>
            <Radio.Group
              value={provider.key}
              onChange={(e) => handleProviderChange(e.target.value)}
              style={{ width: '100%' }}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {PROVIDERS.map((p) => (
                  <Radio.Button
                    key={p.key}
                    value={p.key}
                    style={{
                      width: '100%', height: 'auto', padding: '12px 16px',
                      display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: 2 }}>
                      <ApiOutlined style={{ marginRight: 8 }} />
                      {p.label}
                    </div>
                    <Text type="secondary" style={{ fontSize: 12 }}>{p.desc}</Text>
                  </Radio.Button>
                ))}
              </Space>
            </Radio.Group>
            <Button type="primary" block onClick={() => setStep(1)}>
              下一步
            </Button>
          </Space>
        )}

        {/* Step 1: 填写配置 */}
        {step === 1 && (
          <Space direction="vertical" style={{ width: '100%' }} size={16}>
            <div>
              <Text strong>API Key</Text>
              <Input.Password
                placeholder="输入你的 API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ marginTop: 4 }}
              />
              {provider.key === 'ollama_local' && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  本地 Ollama 通常不需要 API Key，留空即可
                </Text>
              )}
            </div>
            <div>
              <Text strong>Base URL</Text>
              <Input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                style={{ marginTop: 4 }}
              />
            </div>
            <div>
              <Text strong>模型名称</Text>
              <Input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                style={{ marginTop: 4 }}
                placeholder="如 gpt-4o-mini, deepseek-chat, glm-4.7"
              />
            </div>
            <div>
              <Text strong>Tavily 搜索 API Key（可选）</Text>
              <Input.Password
                placeholder="用于联网搜索功能，可稍后配置"
                value={tavilyKey}
                onChange={(e) => setTavilyKey(e.target.value)}
                style={{ marginTop: 4 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                <SearchOutlined /> 在 <a href="https://tavily.com" target="_blank">tavily.com</a> 免费注册获取（1000次/月）
              </Text>
            </div>
            <Space>
              <Button onClick={() => setStep(0)}>上一步</Button>
              <Button type="primary" onClick={() => setStep(2)} disabled={!apiKey && provider.key !== 'ollama_local'}>
                下一步
              </Button>
            </Space>
          </Space>
        )}

        {/* Step 2: 测试连接 */}
        {step === 2 && (
          <Space direction="vertical" style={{ width: '100%' }} size={16}>
            <Paragraph>点击下方按钮测试与 AI 服务的连接。</Paragraph>
            <Card size="small" style={{ background: '#fafafa' }}>
              <Text type="secondary">提供商：</Text><Text>{provider.label}</Text><br />
              <Text type="secondary">Base URL：</Text><Text copyable>{baseUrl}</Text><br />
              <Text type="secondary">模型：</Text><Text code>{model}</Text>
            </Card>
            <Button
              type="primary"
              loading={testing}
              onClick={handleTest}
              icon={<ApiOutlined />}
              block
            >
              测试连接
            </Button>
            {testResult && (
              <Alert
                type={testResult.ok ? 'success' : 'error'}
                message={testResult.ok ? '连接成功' : '连接失败'}
                description={testResult.message}
                showIcon
              />
            )}
            <Space>
              <Button onClick={() => setStep(1)}>上一步</Button>
              <Button
                type="primary"
                onClick={handleSave}
                loading={saving}
                disabled={!!(testResult && !testResult.ok)}
              >
                保存并开始使用
              </Button>
            </Space>
          </Space>
        )}

        {/* Step 3: 完成 */}
        {step === 3 && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
            <Title level={4}>配置完成！</Title>
            <Paragraph type="secondary">
              你可以随时在设置页面修改配置。
            </Paragraph>
            <Button type="primary" icon={<RocketOutlined />} onClick={onComplete} size="large">
              进入应用
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
