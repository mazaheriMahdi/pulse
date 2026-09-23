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
        Some(Self::new(
            buf[2],
            buf[3],
            buf[4],
            buf[5],
            buf[6],
            buf[7],
        ))
    }
}

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
    fn test_decode_defense_in_depth_clamping() {
        // Corrupted wire bytes > 100 for percentages must be clamped to 100 during decode
        let corrupt_wire = [MAGIC_0, MAGIC_1, 150, 75, 220, 180, 80, 250];
        let decoded = TelemetryPacket::decode(&corrupt_wire).expect("valid magic should decode");
        assert_eq!(decoded.cpu_percent, 100);
        assert_eq!(decoded.cpu_temp_c, 75);
        assert_eq!(decoded.ram_percent, 100);
        assert_eq!(decoded.gpu_percent, 100);
        assert_eq!(decoded.gpu_temp_c, 80);
        assert_eq!(decoded.battery_percent, 100);
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
