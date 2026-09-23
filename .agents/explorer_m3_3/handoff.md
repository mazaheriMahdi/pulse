# Handoff Report: Pure Parsing Architecture & Unit Test Suite for `gadget-host`

**Explorer**: `explorer_m3_3` (Explorer 3 — Milestone 3: Host Telemetry & Common Protocol)  
**Workspace**: `/home/mahdi/Programming/perfomance-monitor`  
**Timestamp**: 2026-09-22T18:44:00Z  
**Type**: Hard Handoff  

---

## 1. Observation

### 1.1 Current Parsing Logic in `software/gadget-host/src/main.rs`

An inspection of `/home/mahdi/Programming/perfomance-monitor/software/gadget-host/src/main.rs` revealed that all parsing logic is directly coupled with file system I/O and process execution:

#### A. CPU Parsing (`CpuSampler::read_stat` lines 59–78)
```rust
59:     fn read_stat() -> Option<(u64, u64)> {
60:         let content = fs::read_to_string("/proc/stat").ok()?;
61:         let first_line = content.lines().next()?;
62:         if !first_line.starts_with("cpu ") {
63:             return None;
64:         }
65: 
66:         let parts: Vec<u64> = first_line[4..]
67:             .split_whitespace()
68:             .filter_map(|s| s.parse::<u64>().ok())
69:             .collect();
70: 
71:         if parts.len() >= 4 {
72:             let idle = parts[3] + parts.get(4).copied().unwrap_or(0); // idle + iowait
73:             let total: u64 = parts.iter().sum();
74:             Some((idle, total))
75:         } else {
76:             None
77:         }
78:     }
```
- Line 60 directly reads `/proc/stat` from the host filesystem.
- Line 61 grabs only the first line (`.lines().next()`).
- Line 66–69 slices `[4..]` and uses `filter_map(|s| s.parse::<u64>().ok())`. If a non-numeric token is present, it is dropped silently, shifting column indices.
- Line 51–53 in `sample()` performs the CPU delta calculation:
  ```rust
  51:                 let busy = delta_total.saturating_sub(delta_idle);
  52:                 let pct = (busy as f64 / delta_total as f64 * 100.0).round();
  53:                 return pct.clamp(0.0, 100.0) as u8;
  ```
  This arithmetic is embedded within state mutation inside `sample(&mut self) -> u8` and cannot be unit-tested without mocking `/proc/stat`.

#### B. RAM Parsing (`read_ram_percent` lines 81–106)
```rust
81: fn read_ram_percent() -> u8 {
82:     if let Ok(content) = fs::read_to_string("/proc/meminfo") {
83:         let mut total: Option<u64> = None;
84:         let mut available: Option<u64> = None;
85: 
86:         for line in content.lines() {
87:             if line.starts_with("MemTotal:") {
88:                 total = line.split_whitespace().nth(1).and_then(|v| v.parse().ok());
89:             } else if line.starts_with("MemAvailable:") {
90:                 available = line.split_whitespace().nth(1).and_then(|v| v.parse().ok());
91:             }
92:             if total.is_some() && available.is_some() {
93:                 break;
94:             }
95:         }
96: 
97:         if let (Some(tot), Some(avail)) = (total, available) {
98:             if tot > 0 {
99:                 let used = tot.saturating_sub(avail);
100:                 let pct = (used as f64 / tot as f64 * 100.0).round();
101:                 return pct.clamp(0.0, 100.0) as u8;
102:             }
103:         }
104:     }
105:     0
106: }
```
- Line 82 hardcodes `fs::read_to_string("/proc/meminfo")`.
- Lines 86–103 iterate string lines and compute the percentage.

#### C. GPU Metrics Parsing (`read_gpu_metrics` lines 135–166)
```rust
135: fn read_gpu_metrics() -> (u8, u8) {
136:     // Query NVIDIA SMI
137:     let output = Command::new("nvidia-smi")
138:         .args([
139:             "--query-gpu=utilization.gpu,temperature.gpu",
140:             "--format=csv,noheader,nounits",
141:         ])
142:         .output();
143: 
144:     if let Ok(out) = output {
145:         if out.status.success() {
146:             let text = String::from_utf8_lossy(&out.stdout);
147:             if let Some(first_line) = text.lines().next() {
148:                 let parts: Vec<&str> = first_line.split(',').map(|s| s.trim()).collect();
149:                 if parts.len() >= 2 {
150:                     let util = parts[0].parse::<u8>().unwrap_or(0);
151:                     let temp = parts[1].parse::<u8>().unwrap_or(0);
152:                     return (util.min(100), temp);
153:                 }
154:             }
155:         }
156:     }
157: 
158:     // Fallback: check AMD sysfs
159:     let amd_busy = fs::read_to_string("/sys/class/drm/card0/device/gpu_busy_percent")
160:         .or_else(|_| fs::read_to_string("/sys/class/drm/card1/device/gpu_busy_percent"))
161:         .ok()
162:         .and_then(|s| s.trim().parse::<u8>().ok())
163:         .unwrap_or(0);
164: 
165:     (amd_busy.min(100), 50)
166: }
```
- Line 137 invokes `Command::new("nvidia-smi")`.
- Lines 147–154 parse CSV stdout `first_line.split(',')`.
- If `parts[0]` or `parts[1]` fails to parse, `.unwrap_or(0)` yields `(0, 0)` instead of falling back to AMD sysfs.
- Lines 159–163 directly parse `/sys/class/drm/card*/device/gpu_busy_percent`.
- Temperature in the AMD path is hardcoded to `50` (line 165).

#### D. CPU Temp & Battery Collectors (lines 108–134, 168–178)
- Lines 120–126: `val_str.trim().parse::<u32>()` -> `(milli / 1000) as u8`.
- Lines 172–174: `content.trim().parse::<u8>()` -> `val.min(100)`.

### 1.2 Current Test and Dependency State
- Executing `cargo test` in `/home/mahdi/Programming/perfomance-monitor/software/gadget-host`:
  ```text
  running 0 tests
  test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
  ```
  Result: Zero unit tests exist in `gadget-host`.
- Executing `grep -rn "sysinfo" software/gadget-host/`:
  The crate `sysinfo = "0.33"` in `software/gadget-host/Cargo.toml` is completely unreferenced in `software/gadget-host/src/main.rs`.
- Executing `timeout 3s cargo run -- --dry-run`:
  ```text
  [Metrics] CPU:   3% (45°C) | GPU:   0% (36°C) | RAM:  55% | Bat: 100%
  ```
  Accurately samples live metrics on the host workstation.

### 1.3 Live Sensor Data on Host Workstation
- Real `/proc/stat` line 1:
  `cpu  1644606 7295 264886 8106142 5994 89831 15817 0 0 0`
- Real `/proc/meminfo` lines:
  `MemTotal:       15597204 kB`
  `MemAvailable:    6976684 kB`
- Real `nvidia-smi` stdout:
  `0, 36`
- Real AMD GPU sysfs (`/sys/class/hwmon/hwmon4/temp1_input`):
  `37000` (37°C)
- Real AMD CPU sysfs (`/sys/class/hwmon/hwmon5/name` -> `k10temp`, `temp1_input`):
  `45125` (45.1°C)

---

## 2. Logic Chain

1. **Decoupling I/O from Logic**:
   - Observations in 1.1.A–D demonstrate that every metric sampler mixes filesystem I/O (`fs::read_to_string`, `fs::read_dir`, `Command::new`) with string manipulation, parsing, and arithmetic.
   - This prevents running unit tests in environments lacking `/proc/stat` or `nvidia-smi` (e.g. CI containers, macOS/Windows developer workstations, mock testing harnesses).
   - By extracting pure functions that take `&str` and return strongly-typed `Option<T>`, 100% of the parsing and math logic can be exercised instantaneously in memory via standard `cargo test`.

2. **Pure CPU Parsing and Delta Mathematics**:
   - Factoring `parse_proc_stat_line(line: &str) -> Option<(u64, u64)>` allows exact verification of tick extraction for 4-field, 10-field, and malformed lines.
   - Factoring `parse_proc_stat(content: &str) -> Option<(u64, u64)>` scans full multi-line `/proc/stat` payloads, finding the aggregate `"cpu "` line while ignoring per-core lines (`"cpu0"`, `"cpu1"`).
   - Factoring `calculate_cpu_percent(prev_idle: u64, prev_total: u64, curr_idle: u64, curr_total: u64) -> u8` isolates the time-delta arithmetic:
     - Detects counter resets/wrap-around via `saturating_sub` (producing 0% instead of integer underflow crash).
     - Handles zero-delta ticks safely (returns 0%).
     - Accurately rounds `0.0..=100.0` with `clamp`.

3. **Pure RAM Parsing**:
   - Splitting RAM processing into:
     - `parse_meminfo_kb(content: &str) -> Option<(u64, u64)>` (extracts `(MemTotal, MemAvailable)` in kB)
     - `parse_meminfo(content: &str) -> Option<u8>` (computes used percentage `(tot - avail) / tot * 100.0`)
   - Guarantees clean handling of missing fields, inverted field ordering, zero total memory, and tab-delimited spacing.

4. **Pure GPU Parsing**:
   - Designing `parse_nvidia_smi(output: &str) -> Option<(u8, u8)>`:
     - Parses standard comma-delimited output (`"35, 48"`).
     - Skips empty lines and non-numeric header lines (e.g. `"utilization.gpu, temperature.gpu"`).
     - Trims accidental unit suffixes (`%`, `C`, `°`).
     - Returns `None` if no valid device reading is found, which cleanly signals `read_gpu_metrics()` to fall back to AMD sysfs rather than yielding phantom `(0, 0)` readings.
   - Supporting `parse_gpu_busy_percent(content: &str) -> Option<u8>`, `parse_hwmon_temp(content: &str) -> Option<u8>`, and `parse_battery_capacity(content: &str) -> Option<u8>` covers all secondary sysfs telemetry paths.

5. **Eliminating Unused Dependencies**:
   - `sysinfo = "0.33"` in `Cargo.toml` is unneeded and slows down compilation. Removing it aligns with `PROJECT.md` Feature 17 and `sub_orch_m3/SCOPE.md`.

---

## 3. Caveats

1. **Linux-Specific Procfs Semantics**:
   - The pure parsers model Linux kernel procfs/sysfs formats (`/proc/stat`, `/proc/meminfo`, sysfs millidegrees). They are cross-platform as pure functions (compiling and testing on any OS), but the actual daemon I/O paths remain Linux-specific.
2. **Multi-GPU Selection**:
   - `parse_nvidia_smi` selects the first valid GPU entry encountered. On multi-GPU systems, GPU 0 (the primary display adapter) will be monitored.
3. **Hardware Fallback Defaults**:
   - When sensors are completely unavailable (e.g. running in a VM without GPU or battery), fallback defaults are preserved: CPU temp = 50°C, GPU = (0%, 50°C), Battery = 100%.

---

## 4. Conclusion & Recommended Implementation Plan

The parsing logic in `software/gadget-host/src/main.rs` should be refactored into pure functions with a comprehensive unit test module.

### 4.1 Recommended Pure Function Signatures & Implementations

```rust
/// Parses a single line from /proc/stat.
/// Returns Some((idle_ticks, total_ticks)) if the line is the aggregate "cpu " line with at least 4 fields.
pub fn parse_proc_stat_line(line: &str) -> Option<(u64, u64)> {
    let rest = line.strip_prefix("cpu ")?;
    let parts: Vec<u64> = rest
        .split_whitespace()
        .filter_map(|s| s.parse::<u64>().ok())
        .collect();

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
pub fn calculate_cpu_percent(prev_idle: u64, prev_total: u64, curr_idle: u64, curr_total: u64) -> u8 {
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
```

---

### 4.2 Recommended Complete Unit Test Suite

Add the following test module directly to `software/gadget-host/src/main.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_proc_stat_line_standard() {
        let line = "cpu  1644606 7295 264886 8106142 5994 89831 15817 0 0 0";
        let (idle, total) = parse_proc_stat_line(line).expect("Should parse standard line");
        assert_eq!(idle, 8106142 + 5994);
        assert_eq!(total, 1644606 + 7295 + 264886 + 8106142 + 5994 + 89831 + 15817);
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
    fn test_parse_battery_capacity() {
        assert_eq!(parse_battery_capacity("95\n"), Some(95));
        assert_eq!(parse_battery_capacity("100\n"), Some(100));
        assert_eq!(parse_battery_capacity("110\n"), Some(100)); // clamped
        assert_eq!(parse_battery_capacity(""), None);
    }
}
```

---

### 4.3 Clean Integration into I/O Daemon Routines

The daemon routines become straightforward wrappers around the pure parsers:

```rust
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

fn read_gpu_metrics() -> (u8, u8) {
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

    let amd_busy = fs::read_to_string("/sys/class/drm/card0/device/gpu_busy_percent")
        .or_else(|_| fs::read_to_string("/sys/class/drm/card1/device/gpu_busy_percent"))
        .ok()
        .and_then(|s| parse_gpu_busy_percent(&s))
        .unwrap_or(0);

    let amd_temp = read_amdgpu_temp().unwrap_or(50);
    (amd_busy, amd_temp)
}
```

---

### 4.4 Removing `sysinfo` Dependency

In `/home/mahdi/Programming/perfomance-monitor/software/gadget-host/Cargo.toml`:
```toml
[package]
name = "gadget-host"
version = "0.1.0"
edition = "2021"

[dependencies]
gadget-common = { path = "../gadget-common" }
serialport = "4.7"
clap = { version = "4.5", features = ["derive"] }
```
Remove `sysinfo = "0.33"` completely.

---

## 5. Verification Method

To independently verify the proposed refactoring:

### 5.1 Unit Test Execution
Execute the test command in `software/gadget-host`:
```bash
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-host
cargo test
```
**Expected Result**: All 18+ pure unit tests pass with `0 failed; 0 ignored; finished in <0.01s`.

### 5.2 Dry-Run Verification Without Regressions
Verify live telemetry sampling on the Linux host:
```bash
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-host
timeout 3s cargo run -- --dry-run
```
**Expected Result**: The daemon starts, initializes the sampler, and prints live host telemetry matching system sensors:
`[Metrics] CPU:  XX% (XX°C) | GPU:  XX% (XX°C) | RAM:  XX% | Bat: 100%`

### 5.3 Invalidation Conditions
This investigation and design would be invalidated if:
1. Linux procfs changes the wire format of `/proc/stat` to remove aggregate `"cpu "` prefix.
2. `nvidia-smi` removes CSV formatting flags (`--format=csv,noheader,nounits`).
