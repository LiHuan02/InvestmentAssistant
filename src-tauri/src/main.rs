#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::thread;
use std::time::Duration;
use tauri_plugin_shell::ShellExt;

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
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let shell = app.shell();
            match shell.sidecar("investment-backend") {
                Ok(command) => match command.spawn() {
                    Ok((_events, child)) => {
                        println!("[Tauri] Sidecar spawned, PID: {:?}", child.pid());
                        thread::spawn(|| {
                            if !wait_for_backend(60) {
                                eprintln!("[Tauri] Backend failed to start within 60 seconds");
                            }
                        });
                    }
                    Err(error) => eprintln!("[Tauri] Sidecar spawn failed: {error}"),
                },
                Err(error) => eprintln!("[Tauri] Sidecar command unavailable: {error}"),
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
