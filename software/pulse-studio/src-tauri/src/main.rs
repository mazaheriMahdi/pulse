// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::UnixStream;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::thread::sleep;
use std::time::Duration;
use tauri::Window;

pub const IPC_SOCKET_PATH: &str = "/tmp/pulse-studio.sock";

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct TelemetryData {
    pub cpu: u8,
    pub cpu_temp: u8,
    pub ram: u8,
    pub gpu: u8,
    pub gpu_temp: u8,
    pub battery: u8,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct StudioConfig {
    pub face: String,
    pub accent: String,
    pub refresh: u8,
    pub brightness: u8,
    pub label: bool,
    pub temp: bool,
    pub units: bool,
    pub invert: bool,
}

struct AppState {
    latest_telemetry: Arc<Mutex<Option<TelemetryData>>>,
    is_connected: Arc<Mutex<bool>>,
}

fn get_config_dir() -> PathBuf {
    if let Ok(home) = std::env::var("HOME") {
        PathBuf::from(home).join(".config").join("pulse-studio")
    } else {
        PathBuf::from("/tmp/pulse-studio")
    }
}

// ── TAURI COMMANDS ────────────────────────────────────────────────────────────

#[tauri::command]
fn get_telemetry(state: tauri::State<'_, AppState>) -> Result<Option<TelemetryData>, String> {
    let t = state.latest_telemetry.lock().map_err(|e| e.to_string())?;
    Ok(t.clone())
}

#[tauri::command]
fn is_daemon_connected(state: tauri::State<'_, AppState>) -> bool {
    state.is_connected.lock().map(|c| *c).unwrap_or(false)
}

#[tauri::command]
fn send_config(config: StudioConfig) -> Result<String, String> {
    // Map face string to face_id
    let face_id: u8 = match config.face.as_str() {
        "cpu" => 0,
        "gpu" => 1,
        "dual" => 2,
        "ram" => 3,
        "thermal" => 4,
        "minimal" => 5,
        "disk" => 3,
        "network" => 0,
        _ => 2,
    };

    // Map accent color hex to accent_color_id
    let accent_color_id: u8 = match config.accent.to_lowercase().as_str() {
        "#d71921" => 1, // Red
        "#ff5a00" => 2, // Orange
        "#2ee6c5" => 3, // Cyan
        "#8b8cf9" => 4, // Purple
        "#ffc247" => 5, // Gold
        _ => 0,         // White
    };

    let mut flags: u8 = 0;
    if config.label {
        flags |= gadget_common::FLAG_SHOW_LABEL;
    }
    if config.temp {
        flags |= gadget_common::FLAG_SHOW_TEMP;
    }
    if config.units {
        flags |= gadget_common::FLAG_SHOW_UNITS;
    }
    if config.invert {
        flags |= gadget_common::FLAG_INVERT;
    }

    let msg = serde_json::json!({
        "type": "config",
        "face_id": face_id,
        "accent_color_id": accent_color_id,
        "brightness": config.brightness,
        "refresh_hz": config.refresh,
        "flags": flags
    });

    let mut stream = UnixStream::connect(IPC_SOCKET_PATH)
        .map_err(|e| format!("Could not connect to gadget daemon: {}", e))?;
    stream
        .set_read_timeout(Some(Duration::from_millis(1500)))
        .ok();

    let payload = serde_json::to_string(&msg).map_err(|e| e.to_string())? + "\n";
    stream
        .write_all(payload.as_bytes())
        .map_err(|e| format!("Write failed: {}", e))?;

    let mut reader = BufReader::new(&mut stream);
    let mut resp = String::new();
    reader
        .read_line(&mut resp)
        .map_err(|e| format!("Read ACK failed: {}", e))?;

    Ok("FLASH_ACK".to_string())
}

#[tauri::command]
fn save_preset(preset: serde_json::Value) -> Result<String, String> {
    let dir = get_config_dir();
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let path = dir.join("presets.json");
    let content = serde_json::to_string_pretty(&preset).map_err(|e| e.to_string())?;
    fs::write(path, content).map_err(|e| e.to_string())?;
    Ok("SAVED".to_string())
}

#[tauri::command]
fn load_preset() -> Result<Option<serde_json::Value>, String> {
    let path = get_config_dir().join("presets.json");
    if path.exists() {
        let content = fs::read_to_string(path).map_err(|e| e.to_string())?;
        let v: serde_json::Value = serde_json::from_str(&content).map_err(|e| e.to_string())?;
        Ok(Some(v))
    } else {
        Ok(None)
    }
}

#[tauri::command]
fn minimize_window(window: Window) {
    window.minimize().ok();
}

#[tauri::command]
fn maximize_window(window: Window) {
    if window.is_maximized().unwrap_or(false) {
        window.unmaximize().ok();
    } else {
        window.maximize().ok();
    }
}

#[tauri::command]
fn close_window(window: Window) {
    window.close().ok();
}

// ── MAIN ENTRYPOINT ───────────────────────────────────────────────────────────

fn main() {
    let latest_telemetry = Arc::new(Mutex::new(None));
    let is_connected = Arc::new(Mutex::new(false));

    let tele_clone = Arc::clone(&latest_telemetry);
    let conn_clone = Arc::clone(&is_connected);

    // Background thread continuously reading telemetry stream from gadget-host daemon
    std::thread::spawn(move || loop {
        match UnixStream::connect(IPC_SOCKET_PATH) {
            Ok(stream) => {
                if let Ok(mut c) = conn_clone.lock() {
                    *c = true;
                }
                let mut reader = BufReader::new(stream);
                loop {
                    let mut line = String::new();
                    match reader.read_line(&mut line) {
                        Ok(0) => break, // EOF / daemon restarted
                        Ok(_) => {
                            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&line) {
                                if val.get("type").and_then(|t| t.as_str()) == Some("telemetry") {
                                    if let (Some(cpu), Some(cpu_t), Some(ram), Some(gpu), Some(gpu_t), Some(bat)) = (
                                        val.get("cpu").and_then(|v| v.as_u64()),
                                        val.get("cpu_temp").and_then(|v| v.as_u64()),
                                        val.get("ram").and_then(|v| v.as_u64()),
                                        val.get("gpu").and_then(|v| v.as_u64()),
                                        val.get("gpu_temp").and_then(|v| v.as_u64()),
                                        val.get("battery").and_then(|v| v.as_u64()),
                                    ) {
                                        let data = TelemetryData {
                                            cpu: cpu as u8,
                                            cpu_temp: cpu_t as u8,
                                            ram: ram as u8,
                                            gpu: gpu as u8,
                                            gpu_temp: gpu_t as u8,
                                            battery: bat as u8,
                                        };
                                        if let Ok(mut t) = tele_clone.lock() {
                                            *t = Some(data);
                                        }
                                    }
                                }
                            }
                        }
                        Err(_) => break,
                    }
                }
            }
            Err(_) => {
                if let Ok(mut c) = conn_clone.lock() {
                    *c = false;
                }
                sleep(Duration::from_millis(500));
            }
        }
    });

    tauri::Builder::default()
        .manage(AppState {
            latest_telemetry,
            is_connected,
        })
        .invoke_handler(tauri::generate_handler![
            get_telemetry,
            is_daemon_connected,
            send_config,
            save_preset,
            load_preset,
            minimize_window,
            maximize_window,
            close_window
        ])
        .run(tauri::generate_context!())
        .expect("error while running pulse-studio");
}
