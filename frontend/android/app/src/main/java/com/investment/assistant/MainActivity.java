package com.investment.assistant;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

/** Starts the embedded backend before loading the Capacitor WebView. */
public class MainActivity extends BridgeActivity {
    private static final int MAX_RETRIES = 90;
    private int retryCount = 0;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Start before BridgeActivity loads the configured localhost URL.
        PythonBackendService.start(getApplicationContext());
        super.onCreate(savedInstanceState);
        waitForBackend();
    }

    private void onBackendReady() {
        // The bundled Capacitor page is already loaded; API calls now use localhost.
    }

    private void waitForBackend() {
        handler.postDelayed(() -> {
            if (PythonBackendService.isReady()) {
                retryCount = 0;
                return;
            }
            if (retryCount++ < MAX_RETRIES) {
                waitForBackend();
            } else {
                onBackendTimeout();
            }
        }, 1000);
    }

    private void onBackendTimeout() {
        WebView webView = bridge != null ? bridge.getWebView() : null;
        if (webView == null) return;

        String error = PythonBackendService.getStartupError();
        String detail = error == null ? "未捕获到 Python 错误，请使用 adb logcat 查看 PythonBackend 日志。" : error;
        webView.loadData(
            "<html><body style='font-family:sans-serif;padding:20px;text-align:center'>" +
            "<h2>启动失败</h2>" +
            "<p>后端服务未能在60秒内启动。</p>" +
            "<p>请检查应用权限后重试。</p>" +
            "<p style='color:#777;font-size:12px;word-break:break-all'>" + detail + "</p>" +
            "</body></html>",
            "text/html",
            "UTF-8"
        );
    }
}
