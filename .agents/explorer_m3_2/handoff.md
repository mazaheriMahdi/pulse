# Milestone 3 Explorer 2 Investigation & Implementation Plan: Sensor Discovery, Fallback Logic, Serial Port Fallback, and Dependency Cleanup

**Explorer Role**: Explorer 2 (`explorer_m3_2`)  
**Milestone**: Milestone 3 ("Host Telemetry & Common Protocol")  
**Target Subsystem**: `software/gadget-host`  
**Workspace**: `/home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_2`  
**Timestamp**: 2026-09-22T22:14:30Z  

---

## 1. Observation

### 1.1 Existing Source Code in `software/gadget-host`

#### A. `software/gadget-host/Cargo.toml`
Inspected `/home/mahdi/Programming/perfomance-monitor/software/gadget-host/Cargo.toml` (lines 1–11):
```toml
[package]
name = "gadget-host"
version = "0.1.0"
edition = "2021"

[dependencies]
gadget-common = { path = "../gadget-common" }
sysinfo = "0.33"
serialport = "4.7"
clap = { version = "4.5", features = ["derive"] }
```
- **Line 8**: `sysinfo = "0.33"` is declared as a dependency.
- **Search result**: Searching across `software/gadget-host/src/` revealed **zero** uses, imports, or references to `sysinfo`.
- `sysinfo` compiles multiple sub-crates (`libc`, `core-foundation-sys`, etc.) that contribute dead weight to compilation and build time.

#### B. CPU Temperature Sampling (`software/gadget-host/src/main.rs:108-133`)
```rust
fn read_cpu_temp() -> u8 {
    // Scan /sys/class/hwmon for k10temp, coretemp, or generic temp input
    for entry in fs::read_dir("/sys/class/hwmon").into_iter().flatten().flatten() {
        let dir = entry.path();
        let name = fs::read_to_string(dir.join("name")).unwrap_or_default();
        let name = name.trim();

        if name == "k10temp" || name == "coretemp" || name == "acpitz" {
            // Read temp1_input or any temp*_input
            for file in fs::read_dir(&dir).into_iter().flatten().flatten() {
                let filename = file.file_name().to_string_lossy().to_string();
                if filename.starts_with("temp") && filename.ends_with("_input") {
                    if let Ok(val_str) = fs::read_to_string(file.path()) {
                        if let Ok(milli) = val_str.trim().parse::<u32>() {
                            let temp = (milli / 1000) as u8;
                            if temp > 0 && temp < 125 {
                                return temp;
                            }
                        }
                    }
                }
            }
        }
    }
    50 // fallback sensible temp
}
```
- **Line 110**: Reads `/sys/class/hwmon` without sorting or prioritizing dedicated silicon drivers over generic ACPI zones.
- **Line 115**: Treats `name == "k10temp"`, `name == "coretemp"`, and `name == "acpitz"` with equal priority. The first directory returned by `fs::read_dir` matching any of the three is evaluated.
- **Lines 119–129**: Traverses files in `&dir` using `fs::read_dir(&dir)` without checking `temp1_input` first or sorting filenames.

#### C. GPU Metrics Sampling (`software/gadget-host/src/main.rs:135-166`)
```rust
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
            if let Some(first_line) = text.lines().next() {
                let parts: Vec<&str> = first_line.split(',').map(|s| s.trim()).collect();
                if parts.len() >= 2 {
                    let util = parts[0].parse::<u8>().unwrap_or(0);
                    let temp = parts[1].parse::<u8>().unwrap_or(0);
                    return (util.min(100), temp);
                }
            }
        }
    }

    // Fallback: check AMD sysfs
    let amd_busy = fs::read_to_string("/sys/class/drm/card0/device/gpu_busy_percent")
        .or_else(|_| fs::read_to_string("/sys/class/drm/card1/device/gpu_busy_percent"))
        .ok()
        .and_then(|s| s.trim().parse::<u8>().ok())
        .unwrap_or(0);

    (amd_busy.min(100), 50)
}
```
- **Line 165**: In the fallback path, temperature is unconditionally hardcoded to `50` (`(amd_busy.min(100), 50)`).
- **Lines 159–160**: Checks only `/sys/class/drm/card0` and `card1`. On dual-GPU systems (e.g. NVIDIA dGPU + AMD iGPU), the AMD device is frequently assigned `card2` or higher.

#### D. Serial Port Opening (`software/gadget-host/src/main.rs:192-211`)
```rust
    let mut port = if !args.dry_run {
        println!("Connecting to serial port {}...", args.port);
        match serialport::new(&args.port, args.baud)
            .timeout(Duration::from_millis(100))
            .open()
        {
            Ok(p) => {
                println!("Connected to gadget successfully!");
                sleep(Duration::from_millis(1500));
                Some(p)
            }
            Err(e) => {
                eprintln!("Warning: Could not open {}: {}", args.port, e);
                eprintln!("Running in dry-run monitor mode.");
                None
            }
        }
    } else {
        None
    };
```
- **Line 13**: CLI arg `port` defaults to `"/dev/ttyUSB0"`.
- **Line 203**: If `/dev/ttyUSB0` is missing, `open()` fails immediately with `serialport::ErrorKind::Io(std::io::ErrorKind::NotFound)`. The host immediately degrades to dry-run monitor mode instead of checking `/dev/ttyACM0` (the standard node assigned by the Linux kernel cdc_acm driver to Arduino Uno boards with ATmega16U2 USB controllers).

---

### 1.2 Live Host Environment Behavior

Direct inspection of `/sys/class/hwmon` and `/sys/class/drm` on the Linux host system revealed:
1. **/sys/class/hwmon directory entries**:
   ```text
   hwmon0: name=ACAD
   hwmon1: name=acpitz (temp1_input: 41000 m°C [41°C], temp2_input: 20000 m°C [20°C ambient])
   hwmon2: name=BAT0
   hwmon3: name=nvme (temp1_input: 36850 m°C [36°C])
   hwmon4: name=amdgpu (temp1_input: 37000 m°C [37°C, edge])
   hwmon5: name=k10temp (temp1_input: 44750 m°C [44.7°C, Tctl])
   hwmon6: name=hp
   hwmon7: name=spd5118 (temp1_input: 44500 m°C [44.5°C])
   hwmon8: name=ucsi_source_psy_USBC000:001
   ```
2. **Directory iteration order**:
   Executing directory reads showed the VFS returning nodes in order: `hwmon8, hwmon6, hwmon4, hwmon2, hwmon0, hwmon7, hwmon5, hwmon3, hwmon1`.
   Because `fs::read_dir` order is non-deterministic and can vary by kernel mount, if `hwmon1` (`acpitz`) is processed and its directory entries visit `temp2_input` first, the daemon reads **20°C** instead of the actual AMD on-die temperature **44.7°C** (`k10temp`).
3. **/sys/class/drm entries**:
   `card1` is the discrete NVIDIA RTX 4050 GPU.  
   `card2` is the integrated AMD Radeon GPU.  
   `/sys/class/drm/card2/device/gpu_busy_percent` exists and is readable (returns `0`).  
   `/sys/class/hwmon/hwmon4` (`amdgpu`) contains `temp1_input` returning `37000` (37°C).
4. **Serial port error classification**:
   Inspection of `serialport-4.10.1/src/posix/error.rs` confirmed:
   ```rust
   E::ENOENT => K::Io(IO::NotFound)
   ```
   When a port device file does not exist, `open()` returns `serialport::Error` where `e.kind == serialport::ErrorKind::Io(std::io::ErrorKind::NotFound)`.

---

## 2. Logic Chain

1. **CPU Temperature Accuracy (R5)**:
   - Dedicated silicon thermal drivers (`k10temp` on AMD and `coretemp` on Intel) expose internal digital thermal sensors (DTS) directly on the CPU package (`Tctl`/`Tdie` or `Package id 0`).
   - ACPI thermal zones (`acpitz`) often report motherboard ambient sensor pins (e.g. `temp2_input = 20°C` on this system).
   - Therefore, `read_cpu_temp()` must enforce a strict priority:
     - **Priority 1**: Scan for dedicated silicon drivers `k10temp` (AMD) or `coretemp` (Intel).
     - **Priority 2**: Only if neither is present, scan for generic `acpitz`.
   - Within any matched hwmon directory:
     - `temp1_input` is the standard primary sensor under the Linux hwmon sysfs specification.
     - `temp1_input` must be queried first. Only if `temp1_input` is absent or out of bounds (1..124°C) should other `temp*_input` files be queried in lexicographical order.

2. **AMD GPU Telemetry Fidelity (R1, R3, R5)**:
   - `read_gpu_metrics()` currently queries `nvidia-smi` first. On systems without an NVIDIA dGPU, or when NVIDIA drivers are unloaded/suspended, it falls back to AMD sysfs.
   - The current AMD fallback hardcodes `50°C` for temperature and checks only `card0` and `card1`.
   - On Linux systems with AMD graphics, the `amdgpu` kernel module registers a hardware monitor in `/sys/class/hwmon` with `name == "amdgpu"` exposing `temp1_input` (edge temperature).
   - Furthermore, `gpu_busy_percent` can reside under `card0`, `card1`, or `card2`.
   - By querying `/sys/class/hwmon` for `name == "amdgpu"` and reading `temp1_input`, the host daemon delivers live, real-time GPU thermal metrics (e.g. 37°C) instead of a synthetic constant, feeding Quadrant 4 dynamically as mandated by R1 and R3.

3. **Plug-and-Play Serial Port Fallback**:
   - Arduino devices commonly enumerate under two distinct driver namespaces:
     - CH340 / FT232 / CP2102 USB-to-UART bridges: `/dev/ttyUSB0`, `/dev/ttyUSB1`, etc.
     - ATmega16U2 / ATmega8U2 USB CDC-ACM (official Uno / Leonardo / Mega): `/dev/ttyACM0`, `/dev/ttyACM1`, etc.
   - If a user runs `gadget-host` without arguments, clap assigns default `port = "/dev/ttyUSB0"`.
   - If opening `/dev/ttyUSB0` fails with `NotFound`, automatically attempting `/dev/ttyACM0` before falling back to dry-run prevents immediate failure when connecting an official Arduino Uno.
   - If the user explicitly configured a custom port via `--port /dev/custom_port`, no fallback should occur, honoring explicit user configuration.

4. **Dependency & Build Cleanliness**:
   - `sysinfo = "0.33"` in `software/gadget-host/Cargo.toml` is unused. All telemetry metrics are collected directly from Linux kernel sysfs (`/proc/stat`, `/proc/meminfo`, `/sys/class/hwmon`, `/sys/class/power_supply`) and `nvidia-smi`.
   - Removing `sysinfo` simplifies dependency resolution, avoids compiling redundant native helper code, and shortens build times.

---

## 3. Caveats

1. **Non-x86 CPU Sensor Names**:
   - On ARM platforms (e.g., Raspberry Pi or Jetson), the CPU temperature sensor is registered under `cpu_thermal` or `soc_thermal` rather than `k10temp` or `coretemp`. In such environments, the fallback to `acpitz` or general default 50°C applies unless `cpu_thermal` is also recognized.
2. **Serial Permission (Linux `dialout` / `uucp` Group)**:
   - If `/dev/ttyUSB0` or `/dev/ttyACM0` exists but the current user lacks read/write permissions (`EACCES`), `serialport` returns `ErrorKind::Io(std::io::ErrorKind::PermissionDenied)`.
   - The fallback logic specifically triggers on `NotFound`, avoiding attempts to switch ports when the root cause is user group permissions.
3. **NVIDIA Temperature Reading Speed**:
   - `nvidia-smi` has an invocation overhead of ~30–40ms. When run on a 1000ms loop, this overhead is minimal (<4% duty cycle). If `nvidia-smi` is unavailable, the fallback to `/sys/class/drm` and `/sys/class/hwmon` is instantaneous (<1ms).

---

## 4. Conclusion & Detailed Implementation Plan

The host telemetry daemon in `software/gadget-host` should be refactored to implement the following changes:

### 4.1 Implementation Specification

#### Step 1: Remove `sysinfo` from `software/gadget-host/Cargo.toml`
Replace lines 6–11 of `software/gadget-host/Cargo.toml`:
```toml
[dependencies]
gadget-common = { path = "../gadget-common" }
serialport = "4.7"
clap = { version = "4.5", features = ["derive"] }
```

#### Step 2: Implement Testable Sensor & Parsing Helpers in `software/gadget-host/src/main.rs`

1. **`parse_hwmon_temp`** (pure helper for unit tests):
   ```rust
   pub fn parse_hwmon_temp(content: &str) -> Option<u8> {
       let milli = content.trim().parse::<u32>().ok()?;
       let temp = (milli / 1000) as u8;
       if temp > 0 && temp < 125 {
           Some(temp)
       } else {
           None
       }
   }
   ```

2. **`read_hwmon_temp`** (checks `temp1_input` first, then sorted `temp*_input`):
   ```rust
   use std::path::{Path, PathBuf};

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
   ```

3. **`read_cpu_temp`** (prioritize `k10temp` and `coretemp` before `acpitz`):
   ```rust
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

       50 // Sensible fallback temp
   }
   ```

4. **`read_gpu_metrics`** (nvidia-smi with AMD GPU hwmon & drm fallback):
   ```rust
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
               if let Ok(val) = s.trim().parse::<u8>() {
                   return val.min(100);
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
               if let Some(first_line) = text.lines().next() {
                   let parts: Vec<&str> = first_line.split(',').map(|s| s.trim()).collect();
                   if parts.len() >= 2 {
                       let util = parts[0].parse::<u8>().unwrap_or(0);
                       let temp = parts[1].parse::<u8>().unwrap_or(0);
                       return (util.min(100), temp);
                   }
               }
           }
       }

       // Fallback: AMD DRM utilization & AMD GPU hwmon temperature
       let amd_busy = read_amd_gpu_busy();
       let amd_temp = read_amd_gpu_temp().unwrap_or(50);

       (amd_busy, amd_temp)
   }
   ```

5. **Serial Port Auto-Fallback in `main()`**:
   ```rust
   fn open_serial_port(port_name: &str, baud: u32) -> Option<Box<dyn serialport::SerialPort>> {
       println!("Connecting to serial port {}...", port_name);
       match serialport::new(port_name, baud)
           .timeout(Duration::from_millis(100))
           .open()
       {
           Ok(p) => {
               println!("Connected to gadget successfully!");
               sleep(Duration::from_millis(1500));
               Some(p)
           }
           Err(e) => {
               let is_not_found = matches!(e.kind, serialport::ErrorKind::Io(std::io::ErrorKind::NotFound))
                   || e.description.to_lowercase().contains("no such file")
                   || e.description.to_lowercase().contains("not found");

               if port_name == "/dev/ttyUSB0" && is_not_found {
                   println!("Port /dev/ttyUSB0 not found, trying fallback /dev/ttyACM0...");
                   match serialport::new("/dev/ttyACM0", baud)
                       .timeout(Duration::from_millis(100))
                       .open()
                   {
                       Ok(p) => {
                           println!("Connected to gadget successfully on /dev/ttyACM0!");
                           sleep(Duration::from_millis(1500));
                           return Some(p);
                       }
                       Err(fallback_err) => {
                           eprintln!("Warning: Fallback /dev/ttyACM0 also failed: {}", fallback_err);
                       }
                   }
               }
               eprintln!("Warning: Could not open {}: {}", port_name, e);
               eprintln!("Running in dry-run monitor mode.");
               None
           }
       }
   }
   ```

6. **Unit Test Suite Additions**:
   Add tests verifying `parse_hwmon_temp`:
   ```rust
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
   ```

---

## 5. Verification Method

### 5.1 Independent Verification Commands

1. **Verify Cargo.toml dependency removal & compilation**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-host
   cargo check
   cargo test
   ```
   *Expected result*: Compiles cleanly with 0 warnings without building `sysinfo`.

2. **Verify live CPU sensor priority**:
   On the test system:
   ```bash
   cat /sys/class/hwmon/hwmon5/temp1_input   # k10temp (e.g. ~44°C)
   cat /sys/class/hwmon/hwmon1/temp2_input   # acpitz ambient (e.g. 20°C)
   cargo run -- --dry-run
   ```
   *Expected result*: The printed CPU temp matches `k10temp` (~44°C), NOT `acpitz` ambient (20°C).

3. **Verify AMD GPU temperature fallback**:
   On a machine without `nvidia-smi` (or running `PATH="" cargo run -- --dry-run`):
   ```bash
   cat /sys/class/hwmon/hwmon4/temp1_input   # amdgpu temp (~37°C)
   PATH="" cargo run -- --dry-run
   ```
   *Expected result*: Printed GPU temp reports live AMD temperature (~37°C) rather than hardcoded 50°C.

4. **Verify serial port fallback behavior**:
   ```bash
   # Test default port fallback when /dev/ttyUSB0 is absent
   cargo run -- --port /dev/ttyUSB0
   ```
   *Expected result*: If `/dev/ttyUSB0` does not exist, logs `Port /dev/ttyUSB0 not found, trying fallback /dev/ttyACM0...`.

### 5.2 Invalidation Conditions
This plan would be invalidated if:
1. Linux kernel changes the sysfs standard for hwmon temperature reporting from millidegrees C to another unit.
2. The gadget protocol deprecates single-byte temperature reporting in favor of signed or floating-point telemetry.
