import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.investment.assistant',
  appName: 'Investment Assistant',
  webDir: 'dist',
  server: {
    url: 'http://localhost:8000',
    cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 0
    }
  }
};

export default config;
