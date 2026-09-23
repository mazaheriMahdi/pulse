# Milestone 3 Explorer 1 Handoff Report: `gadget-common` & Wire Protocol

**Explorer Role**: Protocol & Serialization Explorer (`explorer_m3_1`)  
**Working Directory**: `/home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_1`  
**Timestamp**: 2026-09-22T18:44:00Z  

---

## 1. Observation

### 1.1 Source Code Inspection of `software/gadget-common/src/lib.rs`

The entire contents of `/home/mahdi/Programming/perfomance-monitor/software/gadget-common/src/lib.rs` (lines 1–64) were inspected:

```rust
#![no_std]

pub const MAGIC_0: u8 = 0xAA;
pub const MAGIC_1: u8 = 0x55;
pub const PACKET_LEN: usize = 8;

#[derive(Copy, Clone, Debug, PartialEq, Eq, Default)]
pub struct TelemetryPacket {
    pub cpu_percent: u8,
    pub cpu_temp_c: u8,
    pub ram_percent: u8,
    pub gpu_percent: u8,
    pub gpu_temp_c: u8,
    pub battery_percent: u8, // 0..100
}

impl TelemetryPacket {
    pub fn new(
        cpu: u8,
        cpu_temp: u8,
        ram: u8,
        gpu: u8,
        gpu_temp: u8,
        battery: u8,
    ) -> Self {
        Self {
            cpu_percent: cpu.min(100),
            cpu_temp_c: cpu_temp,
            ram_percent: ram.min(100),
            gpu_percent: gpu.min(100),
            gpu_temp_c: gpu_temp,
            battery_percent: battery.min(100),
        }
    }

    pub fn encode(&self, out: &mut [u8; PACKET_LEN]) {
        out[0] = MAGIC_0;
        out[1] = MAGIC_1;
        out[2] = self.cpu_percent;
        out[3] = self.cpu_temp_c;
        out[4] = self.ram_percent;
        out[5] = self.gpu_percent;
        out[6] = self.gpu_temp_c;
        out[7] = self.battery_percent;
    }

    pub fn decode(buf: &[u8]) -> Option<Self> {
        if buf.len() < PACKET_LEN {
            return None;
        }
        if buf[0] != MAGIC_0 || buf[1] != MAGIC_1 {
            return None;
        }
        Some(Self {
            cpu_percent: buf[2],
            cpu_temp_c: buf[3],
            ram_percent: buf[4],
            gpu_percent: buf[5],
            gpu_temp_c: buf[6],
            battery_percent: buf[7],
        })
    }
}
```

### 1.2 Wire Protocol Constants & Layout

- **`MAGIC_0: u8 = 0xAA`**: Decimal 170, binary `10101010`. Preamble byte with alternating bits for UART clock synchronization and framing detection.
- **`MAGIC_1: u8 = 0x55`**: Decimal 85, binary `01010101`. Complementary alternating bit pattern providing unambiguous frame start demarcation.
- **`PACKET_LEN: usize = 8`**: Total packet length in bytes.
- **Wire Layout (Fixed 8 bytes)**:
  | Byte Offset | Field Name | Type | Value Range | Semantic / Destination |
  |:---:|:---|:---:|:---:|:---|
  | `0` | `MAGIC_0` | `u8` | `0xAA` | Frame Synchronization Preamble 1 |
  | `1` | `MAGIC_1` | `u8` | `0x55` | Frame Synchronization Preamble 2 |
  | `2` | `cpu_percent` | `u8` | `0..=100` | Quadrant 1 (Top-Left): CPU Load (%) |
  | `3` | `cpu_temp_c` | `u8` | `0..=255` | Quadrant 4 (Bottom-Right): CPU Temp (°C) |
  | `4` | `ram_percent` | `u8` | `0..=100` | Quadrant 3 (Bottom-Left): RAM Usage (%) |
  | `5` | `gpu_percent` | `u8` | `0..=100` | Quadrant 2 (Top-Right): GPU Load (%) |
  | `6` | `gpu_temp_c` | `u8` | `0..=255` | Quadrant 4 (Bottom-Right): GPU Temp (°C) |
  | `7` | `battery_percent`| `u8` | `0..=100` | Auxiliary metric (%) |

- **Endianness & Alignment**: All payload fields are single-byte integers (`u8`). There are zero multi-byte endianness dependencies, eliminating host-target mismatch between little-endian x86_64 and 8-bit AVR.
- **Memory Footprint**: `size_of::<TelemetryPacket>() == 6` bytes. In-memory alignment is 1 byte with 0 padding bytes.

### 1.3 Method Analysis

1. **`TelemetryPacket::new(cpu, cpu_temp, ram, gpu, gpu_temp, battery)`**:
   - Uses `u8::min(100)` to clamp `cpu_percent`, `ram_percent`, `gpu_percent`, and `battery_percent` to `0..=100`.
   - Pass-through for `cpu_temp_c` and `gpu_temp_c` as full `u8` (0..=255 °C), which correctly allows hot operational temperatures (>100°C) without artificial clipping.
2. **`TelemetryPacket::encode(&self, out: &mut [u8; PACKET_LEN])`**:
   - Takes a fixed-size reference `&mut [u8; 8]`. The compiler enforces buffer size at compile time, eliminating runtime bounds checking failure.
   - Populates byte 0 (`0xAA`), byte 1 (`0x55`), and bytes 2..7 deterministically.
   - Strictly `#![no_std]` and zero-heap.
3. **`TelemetryPacket::decode(buf: &[u8]) -> Option<Self>`**:
   - Takes a slice `&[u8]`.
   - Rejects slices with `buf.len() < 8` by returning `None`.
   - Validates `buf[0] == 0xAA && buf[1] == 0x55`; returns `None` on mismatch.
   - Decodes bytes 2..7 into struct fields.
   - Does not clamp fields during decode; it unpacks verbatim bytes.

### 1.4 Downstream Consumers

- **`software/gadget-firmware-uno/src/main.rs` (lines 101–134)**:
  Uses an 8-byte sliding window receiver (`let mut rx_buf = [0u8; PACKET_LEN];`). It feeds incoming bytes into `TelemetryPacket::decode(&rx_buf)`. Upon decoding, it updates `dashboard.update(&mut display, current_packet)` and sends `"ACK"` over UART.
- **`software/gadget-host/src/main.rs` (lines 226–230)**:
  Instantiates `TelemetryPacket::new(cpu, cpu_temp, ram, gpu, gpu_temp, bat)`, encodes to `[u8; PACKET_LEN]`, and transmits over serial UART at 57,600 baud.
- **`software/gadget-core/src/ui.rs` (lines 84–90)**:
  Receives `TelemetryPacket` in `Dashboard::update()`.
- **Current Test Coverage in `software/gadget-common`**:
  Command: `cargo test` in `software/gadget-common`:
  ```text
  running 0 tests
  test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
  ```
  Zero unit tests currently exist in `gadget-common`.

---

## 2. Logic Chain

1. **Protocol Sufficiency for 4-Quadrant UI (R1, R3, R5)**:
   - Observation 1.1 and 1.2 demonstrate that `TelemetryPacket` provides:
     - `cpu_percent` -> Quadrant 1 (CPU Load)
     - `gpu_percent` -> Quadrant 2 (GPU Load)
     - `ram_percent` -> Quadrant 3 (RAM Usage)
     - `cpu_temp_c` + `gpu_temp_c` -> Quadrant 4 (Dual Thermals & Peak calculation via `cpu_temp_c.max(gpu_temp_c)`)
   - Every single metric required by R1 and R3 is already present in `TelemetryPacket`.
   - Therefore, **the wire format and struct fields already 100% fulfill all Milestone 3 and project requirements**.

2. **Fixed 8-Byte Wire Format Requirement**:
   - As observed in 1.4, `gadget-firmware-uno` relies on a fixed 8-byte buffer (`rx_buf: [u8; PACKET_LEN]`) in its non-blocking UART state machine.
   - Expanding or changing the wire format would require synchronized re-flashing across all hardware targets, breaking compatibility.
   - Keeping `PACKET_LEN = 8` ensures zero-heap execution, minimal RAM usage (< 100 bytes static SRAM on Uno), and < 1.5ms serial transmission latency at 57,600 baud.

3. **Field Clamping & Robustness Invariant**:
   - In `TelemetryPacket::new()`, Observation 1.3 shows `cpu.min(100)`, `ram.min(100)`, `gpu.min(100)`, and `battery.min(100)` enforce the `0..=100` percentage invariant.
   - In `TelemetryPacket::decode()`, raw wire bytes `buf[2..=7]` are read directly into `Self`.
   - If an implementer keeps `decode()` as-is, `decode()` faithfully unpacks the wire bytes.
   - If an implementer calls `Self::new(buf[2], buf[3], buf[4], buf[5], buf[6], buf[7])` inside `decode()`, any corrupted or out-of-range percentage bytes on the wire (e.g. 150%) are automatically clamped to 100 before reaching the display dashboard. This provides defense-in-depth against UI coordinate overflows without altering wire format or breaking any interface contracts.

4. **Unit Test Strategy for `gadget-common`**:
   - Observation 1.4 confirmed 0 tests exist.
   - Adding a comprehensive `#[cfg(test)] mod tests` module directly in `software/gadget-common/src/lib.rs` provides automated regression verification of:
     1. Round-trip encode/decode equality across all 6 fields.
     2. Value clamping in `TelemetryPacket::new()` (percentages clamped to 100, temps passed through up to 255).
     3. Strict magic header validation (`0xAA 0x55` accepted; wrong magic 0, wrong magic 1, swapped magic, all-zeros, all-ones rejected).
     4. Short buffer rejection (lengths 0, 1, 2, 7 return `None`).
     5. Over-length buffer tolerance (slices >= 8 bytes decode successfully).
     6. Edge cases and temperature extremes (all 0s, max 255°C, high normal 105°C).
     7. Trait derivations (`Default`, `Clone`, `Copy`, `PartialEq`, `Eq`, `Debug`).

---

## 3. Caveats

1. **Check-Summing**:
   - The current protocol does not include a CRC-8 or XOR checksum byte. Integrity validation relies on the 2-byte magic header (`0xAA 0x55`) and fixed 8-byte framing. Over short direct USB connections at 57,600 baud this is sufficient, but bitflips in the payload bytes 2..7 will pass `decode()`.
2. **`decode()` Sanitization vs Verbatim Unpacking**:
   - Currently, `decode()` does not call `Self::new()`, meaning a payload with `cpu_percent = 250` over the wire will deserialize to `cpu_percent = 250`. In our recommendation, we detail why calling `Self::new()` inside `decode()` is a safe, recommended defense-in-depth improvement.
3. **Firmware Constraints**:
   - `software/gadget-common` is compiled with `#![no_std]`. Any unit test module must continue to allow `#![no_std]` compilation when building firmware for AVR target (`avr-none`).

---

## 4. Conclusion & Detailed Action Plan

### 4.1 Struct Assessment
**No changes to `TelemetryPacket` struct fields or wire format are needed.** The existing struct:
```rust
pub struct TelemetryPacket {
    pub cpu_percent: u8,
    pub cpu_temp_c: u8,
    pub ram_percent: u8,
    pub gpu_percent: u8,
    pub gpu_temp_c: u8,
    pub battery_percent: u8,
}
```
and constants (`MAGIC_0 = 0xAA`, `MAGIC_1 = 0x55`, `PACKET_LEN = 8`) strictly fulfill all requirements.

### 4.2 Optional Polish in `decode()`
Recommended change for the implementer: update `decode()` to delegate to `Self::new()`:
```rust
    pub fn decode(buf: &[u8]) -> Option<Self> {
        if buf.len() < PACKET_LEN {
            return None;
        }
        if buf[0] != MAGIC_0 || buf[1] != MAGIC_1 {
            return None;
        }
        Some(Self::new(
            buf[2],
            buf[3],
            buf[4],
            buf[5],
            buf[6],
            buf[7],
        ))
    }
```
This guarantees that all percentage fields remain `<= 100` even if corrupted wire data arrives over the serial link.

### 4.3 Proposed Unit Test Suite Implementation

The following complete test module should be added to `software/gadget-common/src/lib.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_roundtrip_all_fields() {
        let original = TelemetryPacket::new(45, 68, 72, 85, 62, 95);
        let mut buf = [0u8; PACKET_LEN];
        original.encode(&mut buf);

        // Verify wire layout bytes explicitly
        assert_eq!(buf[0], MAGIC_0);
        assert_eq!(buf[1], MAGIC_1);
        assert_eq!(buf[2], 45);
        assert_eq!(buf[3], 68);
        assert_eq!(buf[4], 72);
        assert_eq!(buf[5], 85);
        assert_eq!(buf[6], 62);
        assert_eq!(buf[7], 95);

        // Decode and verify round-trip fidelity
        let decoded = TelemetryPacket::decode(&buf).expect("decode should succeed for valid buffer");
        assert_eq!(decoded, original);
        assert_eq!(decoded.cpu_percent, 45);
        assert_eq!(decoded.cpu_temp_c, 68);
        assert_eq!(decoded.ram_percent, 72);
        assert_eq!(decoded.gpu_percent, 85);
        assert_eq!(decoded.gpu_temp_c, 62);
        assert_eq!(decoded.battery_percent, 95);
    }

    #[test]
    fn test_percentage_clamping_above_100() {
        // Percentages > 100 must be clamped to 100; temperatures must NOT be clamped
        let packet = TelemetryPacket::new(120, 85, 200, 255, 95, 110);
        assert_eq!(packet.cpu_percent, 100);
        assert_eq!(packet.ram_percent, 100);
        assert_eq!(packet.gpu_percent, 100);
        assert_eq!(packet.battery_percent, 100);
        assert_eq!(packet.cpu_temp_c, 85);
        assert_eq!(packet.gpu_temp_c, 95);
    }

    #[test]
    fn test_percentage_boundary_values() {
        // Test lower and upper bounds (0, 99, 100)
        let p_min = TelemetryPacket::new(0, 20, 0, 0, 25, 0);
        assert_eq!(p_min.cpu_percent, 0);
        assert_eq!(p_min.ram_percent, 0);
        assert_eq!(p_min.gpu_percent, 0);
        assert_eq!(p_min.battery_percent, 0);

        let p_max = TelemetryPacket::new(100, 75, 100, 100, 80, 100);
        assert_eq!(p_max.cpu_percent, 100);
        assert_eq!(p_max.ram_percent, 100);
        assert_eq!(p_max.gpu_percent, 100);
        assert_eq!(p_max.battery_percent, 100);

        let p_edge = TelemetryPacket::new(99, 50, 100, 101, 50, 100);
        assert_eq!(p_edge.cpu_percent, 99);
        assert_eq!(p_edge.ram_percent, 100);
        assert_eq!(p_edge.gpu_percent, 100);
    }

    #[test]
    fn test_magic_header_validation() {
        let valid_raw = [MAGIC_0, MAGIC_1, 10, 20, 30, 40, 50, 60];
        assert!(TelemetryPacket::decode(&valid_raw).is_some());

        // Corrupted first magic byte
        let bad_magic_0 = [0x00, MAGIC_1, 10, 20, 30, 40, 50, 60];
        assert_eq!(TelemetryPacket::decode(&bad_magic_0), None);

        // Corrupted second magic byte
        let bad_magic_1 = [MAGIC_0, 0x00, 10, 20, 30, 40, 50, 60];
        assert_eq!(TelemetryPacket::decode(&bad_magic_1), None);

        // Swapped magic bytes
        let swapped = [MAGIC_1, MAGIC_0, 10, 20, 30, 40, 50, 60];
        assert_eq!(TelemetryPacket::decode(&swapped), None);

        // All zero header
        let zeros = [0x00; PACKET_LEN];
        assert_eq!(TelemetryPacket::decode(&zeros), None);
    }

    #[test]
    fn test_short_buffer_rejection() {
        // Slices strictly shorter than PACKET_LEN (8) must return None
        assert_eq!(TelemetryPacket::decode(&[]), None);
        assert_eq!(TelemetryPacket::decode(&[MAGIC_0]), None);
        assert_eq!(TelemetryPacket::decode(&[MAGIC_0, MAGIC_1]), None);
        assert_eq!(TelemetryPacket::decode(&[MAGIC_0, MAGIC_1, 1, 2, 3]), None);
        assert_eq!(TelemetryPacket::decode(&[MAGIC_0, MAGIC_1, 1, 2, 3, 4, 5]), None);
    }

    #[test]
    fn test_longer_buffer_handling() {
        // Buffers with extra trailing bytes should successfully decode the first 8 bytes
        let stream = [MAGIC_0, MAGIC_1, 10, 20, 30, 40, 50, 60, 0xDE, 0xAD, 0xBE, 0xEF];
        let decoded = TelemetryPacket::decode(&stream).expect("stream decode should succeed");
        assert_eq!(decoded.cpu_percent, 10);
        assert_eq!(decoded.cpu_temp_c, 20);
        assert_eq!(decoded.ram_percent, 30);
        assert_eq!(decoded.gpu_percent, 40);
        assert_eq!(decoded.gpu_temp_c, 50);
        assert_eq!(decoded.battery_percent, 60);
    }

    #[test]
    fn test_edge_cases_and_temperature_extremes() {
        // Zero state
        let zero_pkt = TelemetryPacket::new(0, 0, 0, 0, 0, 0);
        let mut zero_buf = [0u8; PACKET_LEN];
        zero_pkt.encode(&mut zero_buf);
        assert_eq!(zero_buf, [MAGIC_0, MAGIC_1, 0, 0, 0, 0, 0, 0]);
        assert_eq!(TelemetryPacket::decode(&zero_buf), Some(zero_pkt));

        // Max temperature (255 °C)
        let max_pkt = TelemetryPacket::new(100, 255, 100, 100, 255, 100);
        assert_eq!(max_pkt.cpu_temp_c, 255);
        assert_eq!(max_pkt.gpu_temp_c, 255);
        let mut max_buf = [0u8; PACKET_LEN];
        max_pkt.encode(&mut max_buf);
        assert_eq!(max_buf, [MAGIC_0, MAGIC_1, 100, 255, 100, 100, 255, 100]);
        assert_eq!(TelemetryPacket::decode(&max_buf), Some(max_pkt));

        // Typical hot thermal conditions (105°C tjmax)
        let hot_pkt = TelemetryPacket::new(95, 105, 75, 90, 110, 80);
        assert_eq!(hot_pkt.cpu_temp_c, 105);
        assert_eq!(hot_pkt.gpu_temp_c, 110);
    }

    #[test]
    fn test_trait_derivations() {
        // Default
        let def = TelemetryPacket::default();
        assert_eq!(def.cpu_percent, 0);
        assert_eq!(def.cpu_temp_c, 0);
        assert_eq!(def.ram_percent, 0);
        assert_eq!(def.gpu_percent, 0);
        assert_eq!(def.gpu_temp_c, 0);
        assert_eq!(def.battery_percent, 0);

        // Copy and Clone
        let pkt1 = TelemetryPacket::new(10, 20, 30, 40, 50, 60);
        let pkt2 = pkt1;
        assert_eq!(pkt1, pkt2);

        // PartialEq inequality
        let pkt3 = TelemetryPacket::new(11, 20, 30, 40, 50, 60);
        assert_ne!(pkt1, pkt3);
    }
}
```

---

## 5. Verification Method

To verify all findings and test proposals independently:

```bash
# 1. Run unit tests in software/gadget-common
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-common
cargo test

# 2. Check compilation of gadget-common
cargo check

# 3. Check compilation of dependent firmware target
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-firmware-uno
cargo +nightly build

# 4. Check compilation of dependent host daemon
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-host
cargo check
```

### Invalidation Conditions
This investigation and test plan would be invalidated if:
1. `TelemetryPacket` wire length was altered from 8 bytes, breaking firmware UART buffer assumptions.
2. Floating-point or multi-byte metrics were introduced into the serial protocol.
