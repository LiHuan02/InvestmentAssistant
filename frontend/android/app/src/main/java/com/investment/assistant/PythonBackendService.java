package com.investment.assistant;

import android.content.Context;
import android.util.Log;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;

/** Starts the lightweight Python HTTP server bundled with the Android APK. */
public final class PythonBackendService {
    private static final String TAG = "PythonBackend";
    private static final int BACKEND_PORT = 8000;
    private static final Object LOCK = new Object();
    private static volatile boolean isStarted = false;
    private static volatile String startupError;
    private static Thread serverThread;

    private PythonBackendService() {}

    public static void start(Context context) {
        synchronized (LOCK) {
            if (isStarted || (serverThread != null && serverThread.isAlive())) return;

            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(context.getApplicationContext()));
                }
                copyAssets(context);
                serverThread = new Thread(() -> runPythonServer(), "investment-python-backend");
                serverThread.setDaemon(true);
                serverThread.start();
                Log.i(TAG, "Python backend starting on port " + BACKEND_PORT);
            } catch (Exception e) {
                startupError = e.toString();
                Log.e(TAG, "Python backend initialization failed", e);
            }
        }
    }

    private static void runPythonServer() {
        try {
            Python py = Python.getInstance();
            PyObject pyModule = py.getModule("android_server");
            pyModule.callAttr("run_server", BACKEND_PORT);
            startupError = "Python server exited before becoming ready";
            Log.e(TAG, startupError);
        } catch (Exception e) {
            startupError = e.toString();
            Log.e(TAG, "Python backend failed", e);
        }
    }

    public static boolean isReady() {
        if (startupError != null) return false;
        try {
            java.net.URL url = new java.net.URL("http://127.0.0.1:" + BACKEND_PORT + "/api/v1/health");
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(1000);
            conn.setReadTimeout(1000);
            conn.setRequestMethod("GET");
            int code = conn.getResponseCode();
            conn.disconnect();
            return code == 200;
        } catch (Exception e) {
            return false;
        }
    }

    public static String getStartupError() {
        return startupError;
    }

    public static int getPort() {
        return BACKEND_PORT;
    }

    private static void copyAssets(Context context) {
        File targetDir = new File(context.getFilesDir(), "backend");
        if (!targetDir.exists() && !targetDir.mkdirs()) {
            throw new IllegalStateException("Unable to create " + targetDir.getAbsolutePath());
        }
        Log.i(TAG, "Backend files ready at: " + targetDir.getAbsolutePath());
    }
}
