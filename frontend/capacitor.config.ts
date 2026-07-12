import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.investment.assistant',
  appName: 'Investment Assistant',
  webDir: 'dist',
  server: {
    url: 'http://127.0.0.1:8000',
    cleartext: true,
    androidScheme: 'http'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 0
    }
  }
};

export default config;
