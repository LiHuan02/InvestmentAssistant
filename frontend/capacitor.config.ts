import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.investment.assistant',
  appName: 'Investment Assistant',
  webDir: 'dist',
  // Keep the bundled Capacitor page as the initial document. Android starts
  // its Python API asynchronously; the frontend talks to 127.0.0.1 directly.
  plugins: {
    SplashScreen: {
      launchShowDuration: 0
    }
  }
};

export default config;
