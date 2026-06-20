#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::thread;
use std::time::Duration;

fn wait_for_backend(url: &str, max_retries: u32) -> bool {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .unwrap();

    for i in 0..max_retries {
        thread::sleep(Duration::from_secs(1));
        match client.get(url).send() {
            Ok(resp) if resp.status().is_success() => {
                println!("[Tauri] Backend ready after {}s", i + 1);
                return true;
            }
            _ => {
                println!("[Tauri] Waiting for backend... ({}/{})", i + 1, max_retries);
            }
        }
    }
    false
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let handle = app.handle().clone();

            // Spawn sidecar
            let sidecar = handle.shell().sidecar("investment-backend");
            match sidecar {
                Ok(cmd) => {
                    match cmd.spawn() {
                        Ok((_rx, child)) => {
                            println!("[Tauri] Sidecar started (pid: {:?})", child.pid());

                            // Wait for backend health in a separate thread
                            let health_url = "http://localhost:8000/api/v1/health".to_string();
                            thread::spawn(move || {
                                if !wait_for_backend(&health_url, 30) {
                                    eprintln!("[Tauri] Backend failed to start within 30s");
                                }
                            });
                        }
                        Err(e) => {
                            eprintln!("[Tauri] Failed to spawn sidecar: {}", e);
                        }
                    }
                }
                Err(e) => {
                    eprintln!("[Tauri] Sidecar not found: {}", e);
                }
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
