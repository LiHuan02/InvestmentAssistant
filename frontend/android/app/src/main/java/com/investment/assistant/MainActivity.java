package com.investment.assistant;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.webkit.WebView;
import android.widget.ProgressBar;
import android.widget.TextView;
import com.getcapacitor.BridgeActivity;

/**
 * Main Activity that:
 * 1. Starts the embedded Python backend
 * 2. Waits for it to become ready (health check polling)
 * 3. Loads the Capacitor WebView pointing to localhost
 */
public class MainActivity extends BridgeActivity {

    private static final int MAX_RETRIES = 30;
    private int retryCount = 0;
    private Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Start Python backend
        PythonBackendService.start(getApplicationContext());

        // Poll for backend readiness
        waitForBackend();
    }

    private void waitForBackend() {
        handler.postDelayed(() -> {
            if (PythonBackendService.isReady()) {
                onBackendReady();
            } else if (retryCount < MAX_RETRIES) {
                retryCount++;
                waitForBackend();
            } else {
                onBackendTimeout();
            }
        }, 1000);
    }

    private void onBackendReady() {
        // Backend is ready, Capacitor will load the WebView
        // The WebView is configured to point to localhost:8000
        runOnUiThread(() -> {
            View splash = findViewById(android.R.id.content);
            if (splash != null) {
                splash.setAlpha(1.0f);
            }
        });
    }

    private void onBackendTimeout() {
        runOnUiThread(() -> {
            // Show error in WebView
            WebView webView = bridge != null ? bridge.getWebView() : null;
            if (webView != null) {
                webView.loadData(
                    "<html><body style='font-family:sans-serif;padding:20px;text-align:center'>" +
                    "<h2>启动失败</h2>" +
                    "<p>后端服务未能在30秒内启动。</p>" +
                    "<p>请重启应用重试。</p>" +
                    "</body></html>",
                    "text/html",
                    "UTF-8"
                );
            }
        });
    }
}
