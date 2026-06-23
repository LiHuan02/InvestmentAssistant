#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::thread;
use std::time::Duration;
use tauri_plugin_shell::ShellExt;

fn wait_for_backend(max_retries: u32) -> bool {
    for i in 0..max_retries {
        thread::sleep(Duration::from_secs(1));
        match reqwest::blocking::get("http://localhost:8000/api/v1/health") {
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
            let shell = app.shell();

            match shell.sidecar("investment-backend") {
                Ok(cmd) => {
                    match cmd.spawn() {
                        Ok((_rx, mut child)) => {
                            println!("[Tauri] Sidecar spawned, PID: {:?}", child.id());

                            // Monitor sidecar process
                            std::thread::spawn(move || {
                                let status = child.wait();
                                match status {
                                    Ok(exit_status) => {
                                        if !exit_status.success() {
                                            eprintln!("[Tauri] Sidecar exited with: {}", exit_status);
                                        }
                                    }
                                    Err(e) => eprintln!("[Tauri] Sidecar wait error: {}", e),
                                }
                            });

                            // Poll for backend readiness
                            std::thread::spawn(|| {
                                if !wait_for_backend(60) {
                                    eprintln!("[Tauri] Backend failed to start within 60 seconds");
                                }
                            });
                        }
                        Err(e) => {
                            eprintln!("[Tauri] Spawn failed: {}", e);
                        }
                    }
                }
                Err(e) => eprintln!("[Tauri] Sidecar not found: {}", e),
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
