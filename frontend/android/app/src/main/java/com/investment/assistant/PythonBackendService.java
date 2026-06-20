package com.investment.assistant;

import android.content.Context;
import android.util.Log;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;

/**
 * Manages the embedded Python backend (FastAPI) via Chaquopy.
 * Starts the Python server in a background thread and provides
 * health check functionality.
 */
public class PythonBackendService {
    private static final String TAG = "PythonBackend";
    private static final int BACKEND_PORT = 8000;
    private static boolean isStarted = false;
    private static Thread serverThread;

    public static synchronized void start(Context context) {
        if (isStarted) return;

        // Initialize Chaquopy Python
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(context));
        }

        // Copy project files to app's internal storage
        copyAssets(context);

        // Start FastAPI in a background thread
        serverThread = new Thread(() -> {
            try {
                Python py = Python.getInstance();
                PyObject pyModule = py.getModule("android_server");
                pyModule.callAttr("run_server", BACKEND_PORT);
            } catch (Exception e) {
                Log.e(TAG, "Python backend failed", e);
            }
        });
        serverThread.setDaemon(true);
        serverThread.start();
        isStarted = true;
        Log.i(TAG, "Python backend starting on port " + BACKEND_PORT);
    }

    public static boolean isReady() {
        if (!isStarted) return false;
        try {
            java.net.URL url = new java.net.URL("http://localhost:" + BACKEND_PORT + "/api/v1/health");
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(1000);
            conn.setReadTimeout(1000);
            int code = conn.getResponseCode();
            conn.disconnect();
            return code == 200;
        } catch (Exception e) {
            return false;
        }
    }

    public static int getPort() {
        return BACKEND_PORT;
    }

    private static void copyAssets(Context context) {
        // Copy backend Python files from assets to internal storage
        File targetDir = new File(context.getFilesDir(), "backend");
        if (!targetDir.exists()) {
            targetDir.mkdirs();
        }
        // Chaquopy handles Python path automatically via the pip requirements
        Log.i(TAG, "Backend files ready at: " + targetDir.getAbsolutePath());
    }
}
