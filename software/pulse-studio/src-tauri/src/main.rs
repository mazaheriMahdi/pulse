// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
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
    #[serde(default)]
    pub net_up: u8,
    #[serde(default)]
    pub net_dn: u8,
    #[serde(default)]
    pub peak_up: u8,
    #[serde(default)]
    pub peak_dn: u8,
    #[serde(default)]
    pub iface: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct BootStatus {
    pub step: u8,
    pub label: String,
    pub detail: String,
    pub is_connected: bool,
}

impl Default for BootStatus {
    fn default() -> Self {
        Self {
            step: 1,
            label: "SCANNING HARDWARE BUS".to_string(),
            detail: "Searching for PULSE gadget on serial ports...".to_string(),
            is_connected: false,
        }
    }
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
    boot_status: Arc<Mutex<BootStatus>>,
}

fn get_config_dir() -> PathBuf {
    if let Ok(home) = std::env::var("HOME") {
        PathBuf::from(home).join(".config").join("pulse-studio")
    } else {
        PathBuf::from("/tmp/pulse-studio")
    }
}

/// Locates the `gadget-host` binary
fn find_host_binary() -> Option<PathBuf> {
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let candidate = dir.join("gadget-host");
            if candidate.exists() {
                return Some(candidate);
            }
        }
    }

    if let Ok(home) = std::env::var("HOME") {
        let user_bin = PathBuf::from(home).join(".local/bin/gadget-host");
        if user_bin.exists() {
            return Some(user_bin);
        }
    }

    let search_paths = [
        "/usr/local/bin/gadget-host",
        "/usr/bin/gadget-host",
        "/home/mahdi/Programming/perfomance-monitor/software/gadget-host/target/release/gadget-host",
        "/home/mahdi/Programming/perfomance-monitor/software/gadget-host/target/debug/gadget-host",
        "/home/mahdi/Programming/perfomance-monitor/target/release/gadget-host",
        "/home/mahdi/Programming/perfomance-monitor/target/debug/gadget-host",
    ];

    for p in &search_paths {
        let path = PathBuf::from(p);
        if path.exists() {
            return Some(path);
        }
    }

    // Try `which gadget-host`
    if let Ok(output) = Command::new("which").arg("gadget-host").output() {
        if output.status.success() {
            let p_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
            let p = PathBuf::from(p_str);
            if p.exists() {
                return Some(p);
            }
        }
    }

    None
}

/// Ensures the `gadget-host` daemon process is running in the background
fn ensure_host_daemon() -> bool {
    // If socket exists and is connectable, it's already running
    if UnixStream::connect(IPC_SOCKET_PATH).is_ok() {
        return true;
    }

    // Clean up stale socket file if any
    let _ = std::fs::remove_file(IPC_SOCKET_PATH);

    // Try to spawn the binary
    if let Some(bin) = find_host_binary() {
        eprintln!("[Host Manager] Spawning gadget-host: {:?}", bin);
        let _ = Command::new(bin)
            .args(["--baud", "115200"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();
    } else {
        eprintln!("[Host Manager] Binary not found directly, falling back to cargo run...");
        let _ = Command::new("cargo")
            .args(["run", "--manifest-path", "/home/mahdi/Programming/perfomance-monitor/software/gadget-host/Cargo.toml", "--", "--baud", "115200"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();
    }

    // Wait up to 3.5s for the socket to appear
    for _ in 0..35 {
        sleep(Duration::from_millis(100));
        if UnixStream::connect(IPC_SOCKET_PATH).is_ok() {
            eprintln!("[Host Manager] Host daemon is now responding on socket!");
            return true;
        }
    }

    false
}

// ── TAURI COMMANDS ────────────────────────────────────────────────────────────

#[tauri::command]
fn get_boot_status(state: tauri::State<'_, AppState>) -> Result<BootStatus, String> {
    let bs = state.boot_status.lock().map_err(|e| e.to_string())?;
    Ok(bs.clone())
}

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
fn spawn_host_daemon() -> bool {
    ensure_host_daemon()
}

#[tauri::command]
fn send_config(config: StudioConfig) -> Result<String, String> {
    let face_id: u8 = match config.face.as_str() {
        "cpu" => 0,
        "gpu" => 1,
        "dual" => 2,
        "ram" => 3,
        "thermal" => 4,
        "minimal" => 5,
        "network" => 6,
        _ => 2,
    };

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
    let boot_status = Arc::new(Mutex::new(BootStatus::default()));

    let tele_clone = Arc::clone(&latest_telemetry);
    let conn_clone = Arc::clone(&is_connected);
    let boot_clone = Arc::clone(&boot_status);

    // Host supervisor thread
    std::thread::spawn(move || {
        // Step 1: Scan hardware serial ports
        {
            let mut b = boot_clone.lock().unwrap();
            b.step = 1;
            b.label = "SCANNING HARDWARE BUS".to_string();
            let mut detected = "No ports found".to_string();
            for port in &["/dev/ttyUSB1", "/dev/ttyUSB0", "/dev/ttyACM0"] {
                if Path::new(port).exists() {
                    detected = format!("Found PULSE gadget on {}", port);
                    break;
                }
            }
            b.detail = detected;
        }
        sleep(Duration::from_millis(450));

        // Step 2: Ensure host daemon is running
        {
            let mut b = boot_clone.lock().unwrap();
            b.step = 2;
            b.label = "DAEMON INITIALIZATION".to_string();
            b.detail = "Launching background telemetry engine...".to_string();
        }

        ensure_host_daemon();
        sleep(Duration::from_millis(350));

        // Step 3: Connect to daemon IPC stream
        {
            let mut b = boot_clone.lock().unwrap();
            b.step = 3;
            b.label = "SYNCING 115200 BAUD LINK".to_string();
            b.detail = "Establishing high-speed serial handshake...".to_string();
        }

        loop {
            match UnixStream::connect(IPC_SOCKET_PATH) {
                Ok(stream) => {
                    if let Ok(mut c) = conn_clone.lock() {
                        *c = true;
                    }

                    {
                        let mut b = boot_clone.lock().unwrap();
                        b.step = 4;
                        b.label = "TELEMETRY SENSORS ONLINE".to_string();
                        b.detail = "Synchronizing CPU, GPU, RAM, & Thermal metrics...".to_string();
                    }

                    let mut reader = BufReader::new(stream);
                    let mut first_packet = true;

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
                                            let net_up = val.get("net_up").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
                                            let net_dn = val.get("net_dn").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
                                            let peak_up = val.get("peak_up").and_then(|v| v.as_u64()).unwrap_or(48) as u8;
                                            let peak_dn = val.get("peak_dn").and_then(|v| v.as_u64()).unwrap_or(212) as u8;
                                            let iface = val.get("iface").and_then(|v| v.as_str()).unwrap_or("ETH0").to_string();

                                            let data = TelemetryData {
                                                cpu: cpu as u8,
                                                cpu_temp: cpu_t as u8,
                                                ram: ram as u8,
                                                gpu: gpu as u8,
                                                gpu_temp: gpu_t as u8,
                                                battery: bat as u8,
                                                net_up,
                                                net_dn,
                                                peak_up,
                                                peak_dn,
                                                iface,
                                            };
                                            if let Ok(mut t) = tele_clone.lock() {
                                                *t = Some(data);
                                            }

                                            if first_packet {
                                                first_packet = false;
                                                let mut b = boot_clone.lock().unwrap();
                                                b.step = 5;
                                                b.label = "CONNECTED".to_string();
                                                b.detail = "PULSE hardware locked & synced ✓".to_string();
                                                b.is_connected = true;
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
                    // Try to re-ensure host daemon if it crashed
                    ensure_host_daemon();
                }
            }
        }
    });

    tauri::Builder::default()
        .manage(AppState {
            latest_telemetry,
            is_connected,
            boot_status,
        })
        .invoke_handler(tauri::generate_handler![
            get_boot_status,
            get_telemetry,
            is_daemon_connected,
            spawn_host_daemon,
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
