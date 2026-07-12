#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs::OpenOptions;
use std::io::Write;
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

fn write_startup_log(message: &str) {
    if let Ok(base) = std::env::var("LOCALAPPDATA") {
        let dir = std::path::PathBuf::from(base).join("InvestmentAssistant").join("logs");
        let _ = std::fs::create_dir_all(&dir);
        if let Ok(mut file) = OpenOptions::new()
            .create(true)
            .append(true)
            .open(dir.join("tauri.log"))
        {
            let _ = writeln!(file, "{message}");
        }
    }
}

fn wait_for_backend(max_retries: u32) -> bool {
    let client = match reqwest::blocking::Client::builder()
        .connect_timeout(Duration::from_millis(500))
        .timeout(Duration::from_secs(2))
        .build()
    {
        Ok(client) => client,
        Err(error) => {
            eprintln!("[Tauri] Health client creation failed: {error}");
            return false;
        }
    };

    for attempt in 1..=max_retries {
        match client.get("http://127.0.0.1:8000/api/v1/health").send() {
            Ok(resp) if resp.status().is_success() => {
                println!("[Tauri] Backend ready after {attempt}s");
                return true;
            }
            result => {
                println!("[Tauri] Waiting for backend ({attempt}/{max_retries}): {result:?}");
                thread::sleep(Duration::from_secs(1));
            }
        }
    }
    false
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let command = match app.shell().sidecar("investment-backend") {
                Ok(command) => command.args(["--host", "127.0.0.1", "--port", "8000"]),
                Err(error) => {
                    let message = format!("[Tauri] Sidecar lookup failed: {error}");
                    write_startup_log(&message);
                    eprintln!("{message}");
                    return Ok(());
                }
            };

            let (mut events, child) = match command.spawn() {
                Ok(result) => result,
                Err(error) => {
                    let message = format!("[Tauri] Sidecar spawn failed: {error}");
                    write_startup_log(&message);
                    eprintln!("{message}");
                    return Ok(());
                }
            };
            let pid = child.pid();
            let message = format!("[Tauri] Sidecar spawned, PID: {pid}");
            write_startup_log(&message);
            println!("{message}");

            let process = app.state::<BackendProcess>();
            *process.0.lock().unwrap() = Some(child);

            // Keep the receiver alive and surface sidecar startup/runtime errors.
            tauri::async_runtime::spawn(async move {
                while let Some(event) = events.recv().await {
                    let message = match event {
                        CommandEvent::Stdout(bytes) => {
                            format!("[Backend] {}", String::from_utf8_lossy(&bytes).trim())
                        }
                        CommandEvent::Stderr(bytes) => {
                            format!("[Backend] {}", String::from_utf8_lossy(&bytes).trim())
                        }
                        CommandEvent::Error(error) => format!("[Tauri] Sidecar error: {error}"),
                        CommandEvent::Terminated(payload) => {
                            format!("[Tauri] Sidecar terminated: {:?}", payload.code)
                        }
                        _ => continue,
                    };
                    write_startup_log(&message);
                    eprintln!("{message}");
                }
            });

            thread::spawn(|| {
                if !wait_for_backend(60) {
                    let message = "[Tauri] Backend failed to start within 60 seconds";
                    write_startup_log(message);
                    eprintln!("{message}");
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
