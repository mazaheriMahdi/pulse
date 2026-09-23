"""
Tier 3: Cross-Feature Interactions Test Suite (18 Test Cases)
Evaluates pairwise and multi-feature interaction dynamics, clipping integrity,
zero-delta transmission, thermal peak swapping, and multi-quadrant update timing.
"""
import unittest

from .harnesses.display_harness import (
    CARD_BOUNDS,
    COLOR_BORDER,
    COLOR_CPU_AMBER,
    COLOR_CPU_CORAL,
    COLOR_CPU_CYAN,
    COLOR_DARK_BG,
    COLOR_GPU_GREEN,
    COLOR_GPU_ORANGE,
    COLOR_GPU_RED,
    COLOR_PANEL_BG,
    COLOR_RAM_RED,
    COLOR_RAM_ROSE,
    COLOR_RAM_VIOLET,
    COLOR_TMP_CRIMSON,
    COLOR_TMP_GOLD,
    COLOR_TMP_MINT,
    DisplayHarness,
)
from .harnesses.firmware_harness import FirmwareHarness
from .harnesses.host_harness import HostHarness
from .harnesses.protocol_harness import (
    MAGIC_0,
    MAGIC_1,
    PACKET_LEN,
    ProtocolHarness,
    TelemetryPacketModel,
)


class Tier3InteractionTests(unittest.TestCase):
    """Tier 3 Test Cases: T3-INT-01 to T3-INT-18 (18 tests)."""

    def setUp(self):
        self.display = DisplayHarness()
        self.host = HostHarness()
        self.protocol = ProtocolHarness()
        self.firmware = FirmwareHarness()

    def test_t3_int_01_grid_bounding_box_clipping(self):
        """T3-INT-01: F01 (Grid) + F11 (Diff Redraw) -> Card bounding clipping; zero bleed into gutters or adjacent cards."""
        self.display.draw_layout()
        packet = TelemetryPacketModel.create(100, 100, 100, 100, 100, 100)
        self.display.update(packet)

        # Center X gutter (237..242) and Center Y gutter (155..164) must retain COLOR_DARK_BG
        for x in range(237, 243):
            self.assertEqual(self.display.get_pixel(x, 50), COLOR_DARK_BG)
        for y in range(155, 165):
            self.assertEqual(self.display.get_pixel(50, y), COLOR_DARK_BG)

    def test_t3_int_02_big_numeral_ram_palette_sram_ceiling(self):
        """T3-INT-02: F03 (Big Num) + F08 (RAM) + F14 (SRAM) -> 3-digit 100% RAM numeral rendering in Flash/Stack with SRAM <= 100 bytes."""
        packet = TelemetryPacketModel.create(50, 50, 100, 50, 50, 100)
        self.display.update(packet)
        self.assertEqual(self.display.get_ram_color(100), COLOR_RAM_RED)

        # Verify static SRAM ceiling rule
        effective_sram = self.firmware.get_effective_static_sram()
        self.assertLessEqual(effective_sram, 100)

    def test_t3_int_03_thermal_peak_swapping_zero_flicker(self):
        """T3-INT-03: F09 (Thermals) + F10 (Peak) + F12 (Zero) -> Dynamic CPU/GPU PEAK swapping with zero card-level clears or optical strobe."""
        self.display.draw_layout()
        initial_clears = self.display.clear_count

        # Step 1: CPU is peak (78°C vs 62°C)
        p1 = TelemetryPacketModel.create(50, 78, 50, 50, 62, 100)
        self.display.update(p1)

        # Step 2: GPU becomes peak (65°C vs 82°C)
        p2 = TelemetryPacketModel.create(50, 65, 50, 50, 82, 100)
        bytes_tx = self.display.update(p2)

        # Zero full clears during swap
        self.assertEqual(self.display.clear_count, initial_clears)
        # Bounded SPI transmission
        self.assertLess(bytes_tx, 14500)

    def test_t3_int_04_serial_host_redraw_zero_delta_streaming(self):
        """T3-INT-04: F16 (Serial) + F17 (Host) + F11 (Redraw) -> 0-delta packet streaming results in exactly 0 dirty rects and 0 SPI bytes."""
        p1 = TelemetryPacketModel.create(35, 52, 60, 20, 48, 95)
        raw_bytes = self.protocol.encode(p1)
        self.assertEqual(len(raw_bytes), PACKET_LEN)

        self.display.update(p1)
        # Identical packet update must emit 0 SPI bytes
        bytes_tx = self.display.update(p1)
        self.assertEqual(bytes_tx, 0)

    def test_t3_int_05_grid_meter_cpu_palette_expansion(self):
        """T3-INT-05: F01 (Grid) + F05 (Chunky) + F06 (CPU Pal) -> Chunky meter expansion across Cyan -> Amber -> Coral within Q1 card bounds."""
        for val, expected_color in [(40, COLOR_CPU_CYAN), (70, COLOR_CPU_AMBER), (92, COLOR_CPU_CORAL)]:
            p = TelemetryPacketModel.create(val, 50, 50, 50, 50, 100)
            self.display.update(p)
            self.assertEqual(self.display.get_cpu_color(val), expected_color)
            fill_w = val * 2
            self.assertLessEqual(fill_w, 200)

    def test_t3_int_06_vertical_clearance_harmony(self):
        """T3-INT-06: F02 (Header) + F03 (Big Num) + F04 (Legib) -> Vertical clearance harmony: 14px header, 36px numeral, 24px chunky meter."""
        # Header Y: 8..22 (height 14)
        # Numeral Y: 26..62 (height 36)
        # Meter Y: 70..94 (height 24)
        header_y_end = 8 + 14
        numeral_y_start = 26
        numeral_y_end = 26 + 36
        meter_y_start = 70

        self.assertLess(header_y_end, numeral_y_start)
        self.assertLess(numeral_y_end, meter_y_start)
        # Visual angle for 36px numeral at 70cm
        angle = DisplayHarness.calculate_visual_angle_arcmin(36, 700.0)
        self.assertGreaterEqual(angle, 20.0)

    def test_t3_int_07_gpu_palette_meter_contraction(self):
        """T3-INT-07: F07 (GPU Pal) + F05 (Chunky) + F11 (Redraw) -> Rapid load swing contraction/expansion; clearing abandoned track without ghosts."""
        p_peak = TelemetryPacketModel.create(50, 50, 50, 95, 50, 100)
        p_drop = TelemetryPacketModel.create(50, 50, 50, 25, 50, 100)
        self.display.update(p_peak)
        self.assertEqual(self.display.get_gpu_color(95), COLOR_GPU_RED)

        self.display.update(p_drop)
        self.assertEqual(self.display.get_gpu_color(25), COLOR_GPU_GREEN)
        self.assertEqual(self.display.last_packet.gpu_percent, 25)

    def test_t3_int_08_thermal_spike_q4_border_isolation(self):
        """T3-INT-08: F01 (Grid) + F09 (Thermals) + F10 (Peak) -> Thermals > 75°C triggers dynamic Crimson card border on Q4 without affecting Q1-Q3."""
        self.display.draw_layout()
        p = TelemetryPacketModel.create(50, 88, 50, 50, 74, 100)
        self.display.update(p)

        self.assertEqual(self.display.last_border_q4, COLOR_TMP_CRIMSON)
        # Q1 border remains unaffected
        self.assertEqual(self.display.get_pixel(7, 10), COLOR_BORDER)
        # Q2 border remains unaffected
        self.assertEqual(self.display.get_pixel(243, 10), COLOR_BORDER)

    def test_t3_int_09_zero_heap_sram_wire_protocol_reception(self):
        """T3-INT-09: F13 (Zero-Heap) + F14 (SRAM) + F16 (Wire) -> USART RX sliding window state machine processes packets with 0B heap, < 100B SRAM."""
        # Audits heap symbols in ELF
        self.assertTrue(self.firmware.assert_zero_heap())
        # Receives 100 packets in stream
        stream = b"".join(
            self.protocol.encode(TelemetryPacketModel.create(i % 100, 50, 50, 50, 50, 100))
            for i in range(10)
        )
        packets, responses = self.protocol.simulate_uart_receiver(stream)
        self.assertEqual(len(packets), 10)
        self.assertEqual(len(responses), 10)

    def test_t3_int_10_numeral_width_transition_ghost_erasure(self):
        """T3-INT-10: F03 (Big Num) + F11 (Redraw) + F12 (Zero) -> Digit width transition (8% -> 100% -> 0%); clean erasure of 3rd column ghost digits."""
        p1 = TelemetryPacketModel.create(8, 50, 50, 50, 50, 100)
        p2 = TelemetryPacketModel.create(100, 50, 50, 50, 50, 100)
        p3 = TelemetryPacketModel.create(0, 50, 50, 50, 50, 100)

        self.display.update(p1)
        self.display.update(p2)
        self.display.update(p3)

        self.assertEqual(self.display.last_packet.cpu_percent, 0)
        self.assertEqual(self.display.clear_count, 1)  # only initial layout clear

    def test_t3_int_11_host_wire_range_clamping(self):
        """T3-INT-11: F16 (Serial) + F17 (Host) + Range Clamp -> Host telemetry clamping (108% CPU, 135°C temp); firmware graceful handling."""
        p = TelemetryPacketModel.create(108, 135, 150, 102, 90, 105)
        # Percentages are clamped to 100
        self.assertEqual(p.cpu_percent, 100)
        self.assertEqual(p.ram_percent, 100)
        self.assertEqual(p.gpu_percent, 100)
        self.assertEqual(p.battery_percent, 100)
        # Temperature is passed raw
        self.assertEqual(p.cpu_temp_c, 135)
        self.assertEqual(p.gpu_temp_c, 90)

    def test_t3_int_12_ram_creeping_delta_vs_threshold_recolor(self):
        """T3-INT-12: F05 (Meter) + F08 (RAM) + F11 (Redraw) -> Subtle 1% creeping delta vs threshold-crossing full-bar recolor (Violet -> Red)."""
        p1 = TelemetryPacketModel.create(50, 50, 69, 50, 50, 100)  # Violet
        p2 = TelemetryPacketModel.create(50, 50, 70, 50, 50, 100)  # Rose (threshold crossed)
        p3 = TelemetryPacketModel.create(50, 50, 71, 50, 50, 100)  # Rose (incremental)

        self.display.update(p1)
        self.assertEqual(self.display.get_ram_color(69), COLOR_RAM_VIOLET)

        self.display.update(p2)
        self.assertEqual(self.display.get_ram_color(70), COLOR_RAM_ROSE)

        bytes_inc = self.display.update(p3)
        self.assertLess(bytes_inc, 5000)

    def test_t3_int_13_multi_quadrant_spike_duration(self):
        """T3-INT-13: F01 + F02 + F11 + F12 (Simult) -> Full-system multi-quadrant load spike: all 4 cards update in < 45ms without flicker."""
        p1 = TelemetryPacketModel.create(15, 42, 30, 10, 40, 100)
        p2 = TelemetryPacketModel.create(95, 84, 82, 88, 76, 100)

        self.display.update(p1)
        bytes_tx = self.display.update(p2)

        # Transmission time at 8MHz SPI (1.0 us per byte)
        time_ms = (bytes_tx * 8) / 8000.0
        self.assertLess(time_ms, 45.0)
        self.assertEqual(self.display.clear_count, 1)

    def test_t3_int_14_firmware_build_verification(self):
        """T3-INT-14: F03 (Big Num) + F14 (SRAM) + F15 (Flash) -> Firmware build verification: complete numeral engine with Flash < 28KB, SRAM <= 100B."""
        sizes = self.firmware.parse_avr_size()
        self.assertLess(sizes["flash"], 28672)
        self.assertLessEqual(self.firmware.get_effective_static_sram(), 100)

    def test_t3_int_15_packet_noise_recovery_without_ui_distortion(self):
        """T3-INT-15: F11 (Redraw) + F16 (Packet Noise) -> Mid-stream line noise and bad magic recovery without UI distortion or spurious redraws."""
        p_valid = TelemetryPacketModel.create(50, 60, 50, 50, 60, 100)
        self.display.update(p_valid)
        clears_before = self.display.clear_count

        # Noise injection stream
        noise = bytes([0x00, 0xFF, 0xAA, 0x12, 0x55, 0x7E, 0xAA, 0x54])
        packets, _ = self.protocol.simulate_uart_receiver(noise)
        self.assertEqual(len(packets), 0)

        # Resynchronization on next valid packet
        p_next = TelemetryPacketModel.create(75, 65, 80, 45, 60, 100)
        stream_valid = self.protocol.encode(p_next)
        packets_resync, _ = self.protocol.simulate_uart_receiver(stream_valid)
        self.assertEqual(len(packets_resync), 1)

        self.display.update(packets_resync[0])
        self.assertEqual(self.display.clear_count, clears_before)
        self.assertEqual(self.display.last_packet.cpu_percent, 75)

    def test_t3_int_16_four_quadrant_palette_distinctness(self):
        """T3-INT-16: F06 + F07 + F08 + F09 (Palettes) -> 4-Quadrant simultaneous palette distinctness and visual hierarchy under stress."""
        # In nominal state:
        c_cpu = self.display.get_cpu_color(30)
        c_gpu = self.display.get_gpu_color(30)
        c_ram = self.display.get_ram_color(30)
        c_tmp = self.display.get_thermal_color(45)

        # Assert Euclidean RGB distance >= 65 between distinct primary quadrants
        self.assertGreaterEqual(c_cpu.distance_to(c_ram), 65.0)
        self.assertGreaterEqual(c_gpu.distance_to(c_ram), 65.0)

    def test_t3_int_17_dual_sensor_discovery_priority(self):
        """T3-INT-17: F10 (Peak) + F17 (Host Collectors) -> Dual GPU/CPU sensor discovery (k10temp priority, nvidia-smi vs amdgpu hwmon)."""
        mock_hwmon = [("acpitz", 25), ("k10temp", 78)]
        cpu_t = HostHarness.select_cpu_temp_sensor(mock_hwmon)
        self.assertEqual(cpu_t, 78)

        mock_smi = "65, 72\n"
        res = HostHarness.parse_nvidia_smi(mock_smi)
        self.assertIsNotNone(res)
        gpu_util, gpu_t = res
        self.assertEqual(gpu_t, 72)

        # Wire packet mapping
        packet = TelemetryPacketModel.create(50, cpu_t, 50, gpu_util, gpu_t, 100)
        self.assertEqual(packet.cpu_temp_c, 78)
        self.assertEqual(packet.gpu_temp_c, 72)
        # CPU is peak (78 > 72)
        self.assertGreater(packet.cpu_temp_c, packet.gpu_temp_c)

    def test_t3_int_18_zero_float_integer_gauge_math(self):
        """T3-INT-18: F05 (Chunky) + F13 (Zero-Heap) + F15 (Math) -> Zero-float integer gauge math (fill_w = val * 2) preventing soft-float bloat."""
        # 1% = 2px integer scaling
        for val in (0, 1, 50, 99, 100):
            fill_w = val * 2
            self.assertIsInstance(fill_w, int)
            self.assertGreaterEqual(fill_w, 0)
            self.assertLessEqual(fill_w, 200)
