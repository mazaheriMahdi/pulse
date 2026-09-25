use clap::Parser;
use gadget_common::{ConfigurationPacket, TelemetryPacket, PACKET_LEN};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::mpsc::{channel, Sender};
use std::sync::{Arc, Mutex};
use std::thread::sleep;
use std::time::Duration;

pub const IPC_SOCKET_PATH: &str = "/tmp/pulse-studio.sock";

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(tag = "type")]
pub enum IpcMessage {
    #[serde(rename = "telemetry")]
    Telemetry {
        cpu: u8,
        cpu_temp: u8,
        ram: u8,
        gpu: u8,
        gpu_temp: u8,
        battery: u8,
    },
    #[serde(rename = "config")]
    Config {
        face_id: u8,
        accent_color_id: u8,
        brightness: u8,
        refresh_hz: u8,
        flags: u8,
    },
    #[serde(rename = "ack")]
    Ack,
}

#[derive(Parser, Debug)]
#[command(author, version, about = "Desktop Gadget Telemetry Host Daemon")]
struct Args {
    /// Serial port connected to the Arduino Uno
    #[arg(short, long, default_value = "/dev/ttyUSB0")]
    port: String,

    /// Baud rate for communication
    #[arg(short, long, default_value_t = 115200)]
    baud: u32,

    /// Update interval in milliseconds
    #[arg(short, long, default_value_t = 1000)]
    interval_ms: u64,

    /// Run in mock simulation mode without serial port
    #[arg(long)]
    dry_run: bool,
}

/// Parses a single line from /proc/stat.
/// Returns Some((idle_ticks, total_ticks)) if the line starts with aggregate "cpu " with at least 4 fields.
pub fn parse_proc_stat_line(line: &str) -> Option<(u64, u64)> {
    let rest = line.strip_prefix("cpu ")?;
    let mut parts = Vec::new();
    for s in rest.split_whitespace() {
        parts.push(s.parse::<u64>().ok()?);
    }

    if parts.len() >= 4 {
        let idle = parts[3] + parts.get(4).copied().unwrap_or(0); // idle + iowait
        let total: u64 = parts.iter().sum();
        Some((idle, total))
    } else {
        None
    }
}

/// Scans multi-line /proc/stat content and extracts aggregate (idle, total) ticks.
pub fn parse_proc_stat(content: &str) -> Option<(u64, u64)> {
    content
        .lines()
        .find(|l| l.starts_with("cpu "))
        .and_then(parse_proc_stat_line)
}

/// Calculates CPU utilization percentage (0..=100) from previous and current (idle, total) ticks.
pub fn calculate_cpu_percent(
    prev_idle: u64,
    prev_total: u64,
    curr_idle: u64,
    curr_total: u64,
) -> u8 {
    let delta_idle = curr_idle.saturating_sub(prev_idle);
    let delta_total = curr_total.saturating_sub(prev_total);

    if delta_total > 0 {
        let busy = delta_total.saturating_sub(delta_idle);
        let pct = (busy as f64 / delta_total as f64 * 100.0).round();
        pct.clamp(0.0, 100.0) as u8
    } else {
        0
    }
}

/// Parses /proc/meminfo content to extract (MemTotal_kB, MemAvailable_kB).
pub fn parse_meminfo_kb(content: &str) -> Option<(u64, u64)> {
    let mut total: Option<u64> = None;
    let mut available: Option<u64> = None;

    for line in content.lines() {
        if line.starts_with("MemTotal:") {
            total = line.split_whitespace().nth(1).and_then(|v| v.parse().ok());
        } else if line.starts_with("MemAvailable:") {
            available = line.split_whitespace().nth(1).and_then(|v| v.parse().ok());
        }
        if total.is_some() && available.is_some() {
            break;
        }
    }

    match (total, available) {
        (Some(tot), Some(avail)) if tot > 0 => Some((tot, avail)),
        _ => None,
    }
}

/// Parses /proc/meminfo and returns RAM usage percentage (0..=100).
pub fn parse_meminfo(content: &str) -> Option<u8> {
    let (tot, avail) = parse_meminfo_kb(content)?;
    let used = tot.saturating_sub(avail);
    let pct = (used as f64 / tot as f64 * 100.0).round();
    Some(pct.clamp(0.0, 100.0) as u8)
}

/// Parses nvidia-smi CSV stdout and returns (gpu_util_percent, gpu_temp_c).
pub fn parse_nvidia_smi(output: &str) -> Option<(u8, u8)> {
    for line in output.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let parts: Vec<&str> = line.split(',').map(str::trim).collect();
        if parts.len() >= 2 {
            let util_str = parts[0].trim_end_matches('%').trim();
            let temp_str = parts[1].trim_end_matches('C').trim_end_matches('°').trim();
            if let (Ok(util), Ok(temp)) = (util_str.parse::<u8>(), temp_str.parse::<u8>()) {
                return Some((util.min(100), temp));
            }
        }
    }
    None
}

/// Parses AMD GPU busy percentage from DRM sysfs.
pub fn parse_gpu_busy_percent(content: &str) -> Option<u8> {
    content.trim().parse::<u8>().ok().map(|v| v.min(100))
}

/// Parses hwmon temperature in millidegrees Celsius to integer degrees Celsius.
pub fn parse_hwmon_temp(content: &str) -> Option<u8> {
    content
        .trim()
        .parse::<u32>()
        .ok()
        .map(|milli| (milli / 1000) as u8)
        .filter(|&temp| temp > 0 && temp < 125)
}

/// Parses battery capacity percentage (0..=100).
pub fn parse_battery_capacity(content: &str) -> Option<u8> {
    content.trim().parse::<u8>().ok().map(|v| v.min(100))
}

struct CpuSampler {
    prev_idle: u64,
    prev_total: u64,
}

impl CpuSampler {
    fn new() -> Self {
        let (idle, total) = Self::read_stat().unwrap_or((0, 0));
        Self {
            prev_idle: idle,
            prev_total: total,
        }
    }

    fn sample(&mut self) -> u8 {
        if let Some((idle, total)) = Self::read_stat() {
            let pct = calculate_cpu_percent(self.prev_idle, self.prev_total, idle, total);
            self.prev_idle = idle;
            self.prev_total = total;
            pct
        } else {
            0
        }
    }

    fn read_stat() -> Option<(u64, u64)> {
        let content = fs::read_to_string("/proc/stat").ok()?;
        parse_proc_stat(&content)
    }
}

fn read_ram_percent() -> u8 {
    fs::read_to_string("/proc/meminfo")
        .ok()
        .and_then(|c| parse_meminfo(&c))
        .unwrap_or(0)
}

fn read_hwmon_temp(dir: &Path) -> Option<u8> {
    // 1. Prefer temp1_input (standard primary sensor)
    let temp1_path = dir.join("temp1_input");
    if let Ok(content) = fs::read_to_string(&temp1_path) {
        if let Some(temp) = parse_hwmon_temp(&content) {
            return Some(temp);
        }
    }

    // 2. Fallback to other temp*_input in sorted order
    if let Ok(entries) = fs::read_dir(dir) {
        let mut temp_files: Vec<PathBuf> = entries
            .flatten()
            .filter_map(|e| {
                let name = e.file_name().to_string_lossy().to_string();
                if name.starts_with("temp") && name.ends_with("_input") && name != "temp1_input" {
                    Some(e.path())
                } else {
                    None
                }
            })
            .collect();
        temp_files.sort();

        for path in temp_files {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Some(temp) = parse_hwmon_temp(&content) {
                    return Some(temp);
                }
            }
        }
    }

    None
}

fn read_cpu_temp() -> u8 {
    let hwmon_entries: Vec<(PathBuf, String)> = fs::read_dir("/sys/class/hwmon")
        .into_iter()
        .flatten()
        .flatten()
        .filter_map(|entry| {
            let dir = entry.path();
            let name = fs::read_to_string(dir.join("name")).ok()?;
            Some((dir, name.trim().to_string()))
        })
        .collect();

    // Priority 1: Dedicated CPU silicon sensors (AMD k10temp, Intel coretemp)
    for (dir, name) in &hwmon_entries {
        if name == "k10temp" || name == "coretemp" {
            if let Some(temp) = read_hwmon_temp(dir) {
                return temp;
            }
        }
    }

    // Priority 2: Generic ACPI thermal zones
    for (dir, name) in &hwmon_entries {
        if name == "acpitz" {
            if let Some(temp) = read_hwmon_temp(dir) {
                return temp;
            }
        }
    }

    50 // fallback sensible temp
}

fn read_amd_gpu_temp() -> Option<u8> {
    if let Ok(entries) = fs::read_dir("/sys/class/hwmon") {
        for entry in entries.flatten() {
            let dir = entry.path();
            if let Ok(name) = fs::read_to_string(dir.join("name")) {
                if name.trim() == "amdgpu" {
                    if let Some(temp) = read_hwmon_temp(&dir) {
                        return Some(temp);
                    }
                }
            }
        }
    }
    None
}

fn read_amd_gpu_busy() -> u8 {
    for i in 0..8 {
        let path = format!("/sys/class/drm/card{}/device/gpu_busy_percent", i);
        if let Ok(s) = fs::read_to_string(&path) {
            if let Some(val) = parse_gpu_busy_percent(&s) {
                return val;
            }
        }
    }
    0
}

fn read_gpu_metrics() -> (u8, u8) {
    // Query NVIDIA SMI
    let output = Command::new("nvidia-smi")
        .args([
            "--query-gpu=utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ])
        .output();

    if let Ok(out) = output {
        if out.status.success() {
            let text = String::from_utf8_lossy(&out.stdout);
            if let Some(metrics) = parse_nvidia_smi(&text) {
                return metrics;
            }
        }
    }

    // Fallback: AMD DRM utilization & AMD GPU hwmon temperature
    let amd_busy = read_amd_gpu_busy();
    let amd_temp = read_amd_gpu_temp().unwrap_or(50);

    (amd_busy, amd_temp)
}

fn read_battery_percent() -> u8 {
    for bat in &["BAT0", "BAT1", "BAT2"] {
        let cap_path = format!("/sys/class/power_supply/{}/capacity", bat);
        if let Ok(content) = fs::read_to_string(&cap_path) {
            if let Some(val) = parse_battery_capacity(&content) {
                return val;
            }
        }
    }
    100
}

/// Determines whether an automatic fallback to /dev/ttyACM0 should be attempted.
pub fn should_fallback_port(port_name: &str, is_not_found: bool) -> bool {
    port_name == "/dev/ttyUSB0" && is_not_found
}

fn open_serial_port(port_name: &str, baud: u32) -> Option<Box<dyn serialport::SerialPort>> {
    let mut candidates = vec![port_name.to_string()];
    for fallback in &["/dev/ttyUSB1", "/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyACM1"] {
        if !candidates.iter().any(|c| c == *fallback) {
            candidates.push(fallback.to_string());
        }
    }

    if let Ok(available) = serialport::available_ports() {
        for p in available {
            if !candidates.contains(&p.port_name) {
                candidates.push(p.port_name);
            }
        }
    }

    for candidate in &candidates {
        if Path::new(candidate).exists() {
            println!("Probing serial port {}...", candidate);
            match serialport::new(candidate, baud)
                .timeout(Duration::from_millis(100))
                .open()
            {
                Ok(p) => {
                    println!("Connected to gadget successfully on {}!", candidate);
                    sleep(Duration::from_millis(1500));
                    return Some(p);
                }
                Err(e) => {
                    eprintln!("Port {} failed: {}", candidate, e);
                }
            }
        }
    }

    eprintln!("Warning: No active gadget found on any serial port. Running in dry-run monitor mode.");
    None
}

fn start_ipc_server(config_tx: Sender<ConfigurationPacket>) -> Arc<Mutex<Vec<UnixStream>>> {
    let clients = Arc::new(Mutex::new(Vec::<UnixStream>::new()));
    let clients_clone = Arc::clone(&clients);

    let _ = fs::remove_file(IPC_SOCKET_PATH);

    let listener = match UnixListener::bind(IPC_SOCKET_PATH) {
        Ok(l) => {
            println!("IPC Unix Domain Socket server listening on {}", IPC_SOCKET_PATH);
            l
        }
        Err(e) => {
            eprintln!("Warning: Failed to bind IPC socket {}: {}", IPC_SOCKET_PATH, e);
            return clients;
        }
    };
    let _ = listener.set_nonblocking(true);

    std::thread::spawn(move || {
        loop {
            // Accept incoming connections
            match listener.accept() {
                Ok((stream, _)) => {
                    let _ = stream.set_nonblocking(true);
                    if let Ok(mut c) = clients_clone.lock() {
                        c.push(stream);
                    }
                }
                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {}
                Err(e) => {
                    eprintln!("IPC accept error: {}", e);
                }
            }

            // Check incoming requests from clients
            if let Ok(mut c) = clients_clone.lock() {
                let mut to_remove = Vec::new();
                for (idx, stream) in c.iter_mut().enumerate() {
                    let mut reader = BufReader::new(&mut *stream);
                    let mut line = String::new();
                    match reader.read_line(&mut line) {
                        Ok(0) => {
                            to_remove.push(idx);
                        }
                        Ok(_) => {
                            if let Ok(msg) = serde_json::from_str::<IpcMessage>(&line) {
                                match msg {
                                    IpcMessage::Config {
                                        face_id,
                                        accent_color_id,
                                        brightness,
                                        refresh_hz,
                                        flags,
                                    } => {
                                        let cfg = ConfigurationPacket::new(
                                            face_id,
                                            accent_color_id,
                                            brightness,
                                            refresh_hz,
                                            flags,
                                        );
                                        let _ = config_tx.send(cfg);
                                        let ack = serde_json::to_string(&IpcMessage::Ack).unwrap() + "\n";
                                        let _ = stream.write_all(ack.as_bytes());
                                    }
                                    _ => {}
                                }
                            }
                        }
                        Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {}
                        Err(_) => {
                            to_remove.push(idx);
                        }
                    }
                }
                for idx in to_remove.into_iter().rev() {
                    c.remove(idx);
                }
            }

            sleep(Duration::from_millis(50));
        }
    });

    clients
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    println!("==========================================");
    println!("  Desktop Telemetry Host Daemon (Rust)    ");
    println!("==========================================");
    println!("Target Port: {}", args.port);
    println!("Baud Rate:   {}", args.baud);
    println!("Interval:    {} ms", args.interval_ms);
    println!("Dry run:     {}", args.dry_run);
    println!("------------------------------------------");

    let (config_tx, config_rx) = channel::<ConfigurationPacket>();
    let ipc_clients = start_ipc_server(config_tx);
    let mut interval_ms = args.interval_ms;

    let mut port = if !args.dry_run {
        open_serial_port(&args.port, args.baud)
    } else {
        None
    };

    let mut cpu_sampler = CpuSampler::new();
    // Warm up CPU sampler
    sleep(Duration::from_millis(200));

    println!("\nStreaming live telemetry to desktop gadget (Ctrl+C to stop)...\n");

    loop {
        // Handle incoming configuration requests from Studio
        while let Ok(cfg) = config_rx.try_recv() {
            println!(
                "\n[IPC] Received configuration from Studio: Face {}, Accent {}, Brightness {}%, Refresh {}Hz",
                cfg.face_id, cfg.accent_color_id, cfg.brightness, cfg.refresh_hz
            );
            if cfg.refresh_hz > 0 {
                interval_ms = (1000 / cfg.refresh_hz as u64).max(50);
            }
            if let Some(ref mut p) = port {
                let mut buf = [0u8; PACKET_LEN];
                cfg.encode(&mut buf);
                if let Err(e) = p.write_all(&buf) {
                    eprintln!("Failed to write configuration to serial: {}", e);
                } else {
                    println!("[Serial] Injected ConfigurationPacket to gadget successfully!");
                }
            }
        }

        let cpu = cpu_sampler.sample();
        let cpu_temp = read_cpu_temp();
        let ram = read_ram_percent();
        let (gpu, gpu_temp) = read_gpu_metrics();
        let bat = read_battery_percent();

        let packet = TelemetryPacket::new(cpu, cpu_temp, ram, gpu, gpu_temp, bat);

        print!(
            "\r[Metrics] CPU: {:>3}% ({:>2}°C) | GPU: {:>3}% ({:>2}°C) | RAM: {:>3}% | Bat: {:>3}%",
            cpu, cpu_temp, gpu, gpu_temp, ram, bat
        );
        std::io::stdout().flush().ok();

        // Broadcast telemetry to connected Studio IPC clients
        let tele_msg = IpcMessage::Telemetry {
            cpu,
            cpu_temp,
            ram,
            gpu,
            gpu_temp,
            battery: bat,
        };
        if let Ok(json_line) = serde_json::to_string(&tele_msg) {
            let payload = json_line + "\n";
            if let Ok(mut c) = ipc_clients.lock() {
                let mut to_remove = Vec::new();
                for (idx, client) in c.iter_mut().enumerate() {
                    if let Err(_) = client.write_all(payload.as_bytes()) {
                        to_remove.push(idx);
                    }
                }
                for idx in to_remove.into_iter().rev() {
                    c.remove(idx);
                }
            }
        }

        if let Some(ref mut p) = port {
            let mut buf = [0u8; PACKET_LEN];
            packet.encode(&mut buf);
            if let Err(e) = p.write_all(&buf) {
                eprintln!("\nSerial write error: {}", e);
            }
        }

        sleep(Duration::from_millis(interval_ms));
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_proc_stat_line_standard() {
        let line = "cpu  1644606 7295 264886 8106142 5994 89831 15817 0 0 0";
        let (idle, total) = parse_proc_stat_line(line).expect("Should parse standard line");
        assert_eq!(idle, 8106142 + 5994);
        assert_eq!(
            total,
            1644606 + 7295 + 264886 + 8106142 + 5994 + 89831 + 15817
        );
    }

    #[test]
    fn test_parse_proc_stat_line_minimal_4_fields() {
        let line = "cpu  100 200 300 400";
        let (idle, total) = parse_proc_stat_line(line).expect("Should parse 4 fields");
        assert_eq!(idle, 400); // idle with no iowait
        assert_eq!(total, 1000);
    }

    #[test]
    fn test_parse_proc_stat_line_per_core_rejected() {
        // Individual cores start with cpu0, cpu1, etc. and must not match aggregate "cpu "
        let line = "cpu0 104992 351 18801 714581 401 3672 1738 0 0 0";
        assert!(parse_proc_stat_line(line).is_none());
    }

    #[test]
    fn test_parse_proc_stat_line_malformed() {
        assert!(parse_proc_stat_line("").is_none());
        assert!(parse_proc_stat_line("cpu").is_none());
        assert!(parse_proc_stat_line("cpu  10 20 30").is_none()); // only 3 fields
        assert!(parse_proc_stat_line("cpu  abc def ghi jkl").is_none()); // non-numeric
    }

    #[test]
    fn test_parse_proc_stat_full_content() {
        let content = "\
cpu  1000 200 300 4000 500 60 70 0 0 0
cpu0 500 100 150 2000 250 30 35 0 0 0
cpu1 500 100 150 2000 250 30 35 0 0 0
intr 12345678
ctxt 87654321
";
        let (idle, total) = parse_proc_stat(content).expect("Should find cpu aggregate line");
        assert_eq!(idle, 4500); // 4000 + 500
        assert_eq!(total, 6130);
    }

    #[test]
    fn test_calculate_cpu_percent_metrics() {
        // 50% load: total advances by 1000, idle advances by 500
        assert_eq!(calculate_cpu_percent(1000, 2000, 1500, 3000), 50);

        // 100% idle: total advances by 1000, idle advances by 1000
        assert_eq!(calculate_cpu_percent(0, 0, 1000, 1000), 0);

        // 100% load: total advances by 1000, idle advances by 0
        assert_eq!(calculate_cpu_percent(0, 0, 0, 1000), 100);

        // Zero delta / pause
        assert_eq!(calculate_cpu_percent(500, 1000, 500, 1000), 0);

        // Counter reset / reboot
        assert_eq!(calculate_cpu_percent(5000, 10000, 100, 200), 0);

        // Rounding: 334 busy out of 1000 = 33.4% -> 33%
        assert_eq!(calculate_cpu_percent(0, 0, 666, 1000), 33);
        // Rounding: 337 busy out of 1000 = 33.7% -> 34%
        assert_eq!(calculate_cpu_percent(0, 0, 663, 1000), 34);
    }

    #[test]
    fn test_parse_meminfo_standard() {
        let content = "\
MemTotal:       16000000 kB
MemFree:         1000000 kB
MemAvailable:    8000000 kB
Buffers:          500000 kB
Cached:          6500000 kB
";
        assert_eq!(parse_meminfo_kb(content), Some((16000000, 8000000)));
        assert_eq!(parse_meminfo(content), Some(50)); // (16M - 8M) / 16M = 50%
    }

    #[test]
    fn test_parse_meminfo_high_usage() {
        let content = "\
MemTotal:       10000000 kB
MemAvailable:    1000000 kB
";
        assert_eq!(parse_meminfo(content), Some(90)); // 9M used / 10M = 90%
    }

    #[test]
    fn test_parse_meminfo_missing_or_corrupt() {
        assert!(parse_meminfo("").is_none());
        assert!(parse_meminfo("MemTotal: 16000000 kB\n").is_none()); // Missing MemAvailable
        assert!(parse_meminfo("MemAvailable: 8000000 kB\n").is_none()); // Missing MemTotal
        assert!(parse_meminfo("MemTotal: 0 kB\nMemAvailable: 0 kB\n").is_none()); // Zero total
        assert!(parse_meminfo("MemTotal: abc kB\nMemAvailable: 500 kB\n").is_none()); // Non-numeric
    }

    #[test]
    fn test_parse_meminfo_field_order_and_whitespace() {
        // MemAvailable before MemTotal with extra whitespace and tabs
        let content = "MemAvailable:\t   4000000   kB\nMemTotal:    16000000 kB\n";
        assert_eq!(parse_meminfo(content), Some(75)); // (16M - 4M) / 16M = 75%
    }

    #[test]
    fn test_parse_nvidia_smi_standard() {
        let output = "0, 36\n";
        assert_eq!(parse_nvidia_smi(output), Some((0, 36)));

        let output_busy = "  85 ,  68 \n";
        assert_eq!(parse_nvidia_smi(output_busy), Some((85, 68)));
    }

    #[test]
    fn test_parse_nvidia_smi_with_units() {
        let output = "42 %, 55 C\n";
        assert_eq!(parse_nvidia_smi(output), Some((42, 55)));
    }

    #[test]
    fn test_parse_nvidia_smi_multi_gpu() {
        let output = "15, 40\n95, 75\n";
        assert_eq!(parse_nvidia_smi(output), Some((15, 40)));
    }

    #[test]
    fn test_parse_nvidia_smi_header_skipping() {
        let output = "utilization.gpu, temperature.gpu\n28, 51\n";
        assert_eq!(parse_nvidia_smi(output), Some((28, 51)));
    }

    #[test]
    fn test_parse_nvidia_smi_malformed() {
        assert!(parse_nvidia_smi("").is_none());
        assert!(parse_nvidia_smi("NVIDIA-SMI has failed because no devices were found").is_none());
        assert!(parse_nvidia_smi("only_one_value\n").is_none());
        assert!(parse_nvidia_smi("N/A, 50\n").is_none());
    }

    #[test]
    fn test_parse_nvidia_smi_clamping() {
        let output = "150, 60\n";
        assert_eq!(parse_nvidia_smi(output), Some((100, 60)));
    }

    #[test]
    fn test_parse_gpu_busy_percent() {
        assert_eq!(parse_gpu_busy_percent("45\n"), Some(45));
        assert_eq!(parse_gpu_busy_percent(" 120 "), Some(100)); // clamped
        assert_eq!(parse_gpu_busy_percent("bad"), None);
        assert_eq!(parse_gpu_busy_percent(""), None);
    }

    #[test]
    fn test_parse_hwmon_temp() {
        assert_eq!(parse_hwmon_temp("45125\n"), Some(45));
        assert_eq!(parse_hwmon_temp("82875\n"), Some(82));
        assert_eq!(parse_hwmon_temp("0\n"), None); // 0 filtered out
        assert_eq!(parse_hwmon_temp("140000\n"), None); // >125 filtered out
        assert_eq!(parse_hwmon_temp("xyz"), None);
    }

    #[test]
    fn test_parse_hwmon_temp_valid() {
        assert_eq!(parse_hwmon_temp("43000\n"), Some(43));
        assert_eq!(parse_hwmon_temp("82875\n"), Some(82));
        assert_eq!(parse_hwmon_temp("1000\n"), Some(1));
        assert_eq!(parse_hwmon_temp("124000\n"), Some(124));
    }

    #[test]
    fn test_parse_hwmon_temp_out_of_bounds() {
        assert_eq!(parse_hwmon_temp("0\n"), None);
        assert_eq!(parse_hwmon_temp("125000\n"), None);
        assert_eq!(parse_hwmon_temp("200000\n"), None);
    }

    #[test]
    fn test_parse_hwmon_temp_malformed() {
        assert_eq!(parse_hwmon_temp(""), None);
        assert_eq!(parse_hwmon_temp("invalid"), None);
        assert_eq!(parse_hwmon_temp("-5000"), None);
    }

    #[test]
    fn test_parse_battery_capacity() {
        assert_eq!(parse_battery_capacity("95\n"), Some(95));
        assert_eq!(parse_battery_capacity("100\n"), Some(100));
        assert_eq!(parse_battery_capacity("110\n"), Some(100)); // clamped
        assert_eq!(parse_battery_capacity(""), None);
    }

    #[test]
    fn test_should_fallback_port() {
        assert!(should_fallback_port("/dev/ttyUSB0", true));
        assert!(!should_fallback_port("/dev/ttyUSB0", false));
        assert!(!should_fallback_port("/dev/ttyUSB1", true));
        assert!(!should_fallback_port("/dev/ttyACM0", true));
        assert!(!should_fallback_port("/dev/custom_port", true));
    }

    #[test]
    fn test_open_serial_port_nonexistent() {
        let port = open_serial_port("/dev/nonexistent_test_device_9876", 57600);
        assert!(port.is_none());
    }
}
