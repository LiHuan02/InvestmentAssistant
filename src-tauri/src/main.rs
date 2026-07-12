#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

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
            let command = app.shell().sidecar("investment-backend")?.args([
                "--host", "127.0.0.1",
                "--port", "8000",
            ]);
            let (mut events, child) = command.spawn()?;
            let pid = child.pid();
            println!("[Tauri] Sidecar spawned, PID: {pid}");

            let process = app.state::<BackendProcess>();
            *process.0.lock().unwrap() = Some(child);

            // Keep the receiver alive and surface sidecar startup/runtime errors.
            thread::spawn(move || {
                while let Ok(event) = events.recv() {
                    match event {
                        CommandEvent::Stdout(bytes) => {
                            println!("[Backend] {}", String::from_utf8_lossy(&bytes).trim());
                        }
                        CommandEvent::Stderr(bytes) => {
                            eprintln!("[Backend] {}", String::from_utf8_lossy(&bytes).trim());
                        }
                        CommandEvent::Error(error) => eprintln!("[Tauri] Sidecar error: {error}"),
                        CommandEvent::Terminated(payload) => {
                            eprintln!("[Tauri] Sidecar terminated: {:?}", payload.code);
                            break;
                        }
                        _ => {}
                    }
                }
            });

            thread::spawn(|| {
                if !wait_for_backend(60) {
                    eprintln!("[Tauri] Backend failed to start within 60 seconds");
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
