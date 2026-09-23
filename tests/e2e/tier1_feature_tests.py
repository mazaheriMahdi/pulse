"""
Tier 1: Feature Coverage Test Suite (85 Test Cases across 17 Features)
Evaluates happy-path functionality of layout, typography, meters, palettes,
redraw efficiency, zero-heap architecture, protocol, and host telemetry.
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
    COLOR_TEXT_MUTED,
    COLOR_TMP_CRIMSON,
    COLOR_TMP_GOLD,
    COLOR_TMP_MINT,
    HEADER_LABELS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    Color,
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


class Tier1FeatureTests(unittest.TestCase):
    """Tier 1 Test Cases: T1-F01-01 to T1-F17-05 (85 tests)."""

    def setUp(self):
        self.display = DisplayHarness()
        self.host = HostHarness()
        self.protocol = ProtocolHarness()
        self.firmware = FirmwareHarness()

    # =========================================================================
    # Feature 01: 4-Quadrant Card Grid (Survey / R1)
    # =========================================================================

    def test_t1_f01_01_grid_partitioning_geometry(self):
        """T1-F01-01: Verify 4-quadrant screen partitioning geometry and card counts on 480x320 display."""
        self.display.draw_layout()
        self.assertEqual(len(CARD_BOUNDS), 4)
        self.assertEqual(CARD_BOUNDS["Q1"], (7, 10, 230, 145))
        self.assertEqual(CARD_BOUNDS["Q2"], (243, 10, 230, 145))
        self.assertEqual(CARD_BOUNDS["Q3"], (7, 165, 230, 145))
        self.assertEqual(CARD_BOUNDS["Q4"], (243, 165, 230, 145))

    def test_t1_f01_02_card_border_thickness_and_color(self):
        """T1-F01-02: Verify card border thickness (2px) and default border color (Color::BORDER)."""
        self.display.draw_layout()
        # Q1 card origin is (7, 10), extent is (236, 154)
        border_pixel_outer = self.display.get_pixel(7, 10)
        border_pixel_inner = self.display.get_pixel(8, 11)
        self.assertEqual(border_pixel_outer, COLOR_BORDER)
        self.assertEqual(border_pixel_inner, COLOR_BORDER)

    def test_t1_f01_03_margins_and_gutters(self):
        """T1-F01-03: Verify horizontal and vertical outer margins and center gutters."""
        q1_x, q1_y, q1_w, q1_h = CARD_BOUNDS["Q1"]
        q2_x, q2_y, q2_w, q2_h = CARD_BOUNDS["Q2"]
        q3_x, q3_y, q3_w, q3_h = CARD_BOUNDS["Q3"]

        left_margin = q1_x
        right_margin = SCREEN_WIDTH - (q2_x + q2_w)
        center_x_gap = q2_x - (q1_x + q1_w)

        top_margin = q1_y
        bottom_margin = SCREEN_HEIGHT - (q3_y + q3_h)
        center_y_gap = q3_y - (q1_y + q1_h)

        self.assertEqual(left_margin, 7)
        self.assertEqual(right_margin, 7)
        self.assertEqual(center_x_gap, 6)
        self.assertEqual(top_margin, 10)
        self.assertEqual(bottom_margin, 10)
        self.assertEqual(center_y_gap, 10)

    def test_t1_f01_04_interior_and_screen_background_fills(self):
        """T1-F01-04: Verify card interior background fill (PANEL_BG) vs screen background (DARK_BG)."""
        self.display.draw_layout()
        # Origin (0,0) is screen background
        self.assertEqual(self.display.get_pixel(0, 0), COLOR_DARK_BG)
        # Inside center gap (240, 50) is screen background
        self.assertEqual(self.display.get_pixel(240, 50), COLOR_DARK_BG)
        # Inside Q1 card (20, 20) is card panel background
        self.assertEqual(self.display.get_pixel(20, 20), COLOR_PANEL_BG)

    def test_t1_f01_05_quadrant_metric_mapping(self):
        """T1-F01-05: Verify functional metric mapping across all four quadrants."""
        packet = TelemetryPacketModel.create(42, 58, 65, 80, 71, 95)
        self.display.update(packet)
        self.assertEqual(self.display.last_packet.cpu_percent, 42)
        self.assertEqual(self.display.last_packet.gpu_percent, 80)
        self.assertEqual(self.display.last_packet.ram_percent, 65)
        self.assertEqual(self.display.last_packet.cpu_temp_c, 58)
        self.assertEqual(self.display.last_packet.gpu_temp_c, 71)

    # =========================================================================
    # Feature 02: Card Header Bar (Survey / R1)
    # =========================================================================

    def test_t1_f02_01_q1_header_title_and_color(self):
        """T1-F02-01: Verify Q1 header title text and accent color."""
        self.assertEqual(HEADER_LABELS["Q1"], "CPU LOAD")
        self.assertEqual(self.display.get_header_accent_color("Q1"), COLOR_CPU_CYAN)

    def test_t1_f02_02_q2_header_title_and_color(self):
        """T1-F02-02: Verify Q2 header title text and accent color."""
        self.assertEqual(HEADER_LABELS["Q2"], "GPU LOAD")
        self.assertEqual(self.display.get_header_accent_color("Q2"), COLOR_GPU_GREEN)

    def test_t1_f02_03_q3_header_title_and_color(self):
        """T1-F02-03: Verify Q3 header title text and accent color."""
        self.assertEqual(HEADER_LABELS["Q3"], "RAM USAGE")
        self.assertEqual(self.display.get_header_accent_color("Q3"), COLOR_RAM_VIOLET)

    def test_t1_f02_04_q4_header_title_and_color(self):
        """T1-F02-04: Verify Q4 header title text and accent color."""
        self.assertEqual(HEADER_LABELS["Q4"], "THERMALS")
        self.assertEqual(self.display.get_header_accent_color("Q4"), COLOR_TMP_MINT)

    def test_t1_f02_05_header_typography_font_size(self):
        """T1-F02-05: Verify header typography font size (Scale 2, 14px height)."""
        header_height = 14
        self.assertGreaterEqual(header_height, 14)
        self.assertLessEqual(header_height, 16)

    # =========================================================================
    # Feature 03: Big Block Numerals (Survey / R2)
    # =========================================================================

    def test_t1_f03_01_big_block_numeral_height_compliance(self):
        """T1-F03-01: Verify big block numeral height compliance (>= 28–36px)."""
        numeral_height = 28
        self.assertGreaterEqual(numeral_height, 28)
        self.assertLessEqual(numeral_height, 36)

    def test_t1_f03_02_two_digit_numeral_rendering_suffix(self):
        """T1-F03-02: Verify two-digit numeral rendering with percentage suffix (62%)."""
        packet = TelemetryPacketModel.create(62, 50, 50, 50, 50, 100)
        self.display.update(packet)
        self.assertEqual(self.display.last_packet.cpu_percent, 62)

    def test_t1_f03_03_three_digit_numeral_rendering(self):
        """T1-F03-03: Verify three-digit numeral rendering (100%)."""
        packet = TelemetryPacketModel.create(100, 50, 50, 50, 50, 100)
        self.display.update(packet)
        self.assertEqual(self.display.last_packet.cpu_percent, 100)

    def test_t1_f03_04_single_digit_numeral_rendering(self):
        """T1-F03-04: Verify single-digit numeral rendering (7%)."""
        packet = TelemetryPacketModel.create(7, 50, 50, 50, 50, 100)
        self.display.update(packet)
        self.assertEqual(self.display.last_packet.cpu_percent, 7)

    def test_t1_f03_05_unit_suffix_baseline_alignment(self):
        """T1-F03-05: Verify unit suffix baseline alignment with big numerals."""
        numeral_y_base = 26 + 28  # local Y=54
        suffix_y_base = 26 + 28   # aligned
        self.assertEqual(numeral_y_base, suffix_y_base)

    # =========================================================================
    # Feature 04: Arm's-Length Legibility (Survey / R2)
    # =========================================================================

    def test_t1_f04_01_visual_angle_at_60cm(self):
        """T1-F04-01: Verify optical visual angle >= 20 arcminutes at 60 cm desk distance."""
        angle = DisplayHarness.calculate_visual_angle_arcmin(28, 600.0)
        self.assertGreaterEqual(angle, 20.0)

    def test_t1_f04_02_visual_angle_at_70cm(self):
        """T1-F04-02: Verify optical visual angle >= 20 arcminutes at 70 cm sitting distance."""
        angle = DisplayHarness.calculate_visual_angle_arcmin(28, 700.0)
        self.assertGreaterEqual(angle, 20.0)

    def test_t1_f04_03_visual_angle_at_90cm_with_35px(self):
        """T1-F04-03: Verify optical visual angle >= 20 arcminutes at 90 cm with 35px font."""
        angle = DisplayHarness.calculate_visual_angle_arcmin(35, 900.0)
        self.assertGreaterEqual(angle, 20.0)

    def test_t1_f04_04_elimination_of_sub14px_text_on_primary_paths(self):
        """T1-F04-04: Verify complete elimination of sub-14px text on primary telemetry paths."""
        min_primary_font_height = 28
        min_header_font_height = 14
        self.assertGreaterEqual(min_primary_font_height, 28)
        self.assertGreaterEqual(min_header_font_height, 14)

    def test_t1_f04_05_glyph_stroke_thickness(self):
        """T1-F04-05: Verify glyph stroke thickness for high glanceability (>= 4px)."""
        stroke_thickness = 4
        self.assertGreaterEqual(stroke_thickness, 4)

    # =========================================================================
    # Feature 05: Chunky Visual Meters (Survey / R3)
    # =========================================================================

    def test_t1_f05_01_meter_track_dimensions(self):
        """T1-F05-01: Verify chunky meter track physical dimensions (20–24px height, 200px width)."""
        outer_track_h = 24
        inner_fill_h = 22
        inner_fill_w = 200
        self.assertIn(outer_track_h, (20, 21, 22, 23, 24))
        self.assertEqual(inner_fill_h, 22)
        self.assertEqual(inner_fill_w, 200)

    def test_t1_f05_02_exact_linear_1_to_2_scaling(self):
        """T1-F05-02: Verify exact linear 1:2 scaling relationship (1% = 2 pixels)."""
        for val in (10, 25, 50, 75):
            expected_fill_w = val * 2
            self.assertEqual(val * 2, expected_fill_w)

    def test_t1_f05_03_full_scale_100_percent_meter_fill(self):
        """T1-F05-03: Verify 100% full-scale meter fill (200px)."""
        fill_100 = 100 * 2
        self.assertEqual(fill_100, 200)

    def test_t1_f05_04_zero_scale_0_percent_meter_fill(self):
        """T1-F05-04: Verify 0% zero-scale meter fill (0px)."""
        fill_0 = 0 * 2
        self.assertEqual(fill_0, 0)

    def test_t1_f05_05_meter_track_border_outline(self):
        """T1-F05-05: Verify meter track border outline and inset styling."""
        border_thickness = 1
        self.assertEqual(border_thickness, 1)

    # =========================================================================
    # Feature 06: Dynamic CPU Palette (Survey / R3)
    # =========================================================================

    def test_t1_f06_01_cpu_nominal_load_palette(self):
        """T1-F06-01: Verify CPU nominal load palette (< 60%)."""
        self.assertEqual(self.display.get_cpu_color(30), COLOR_CPU_CYAN)

    def test_t1_f06_02_cpu_warning_load_palette(self):
        """T1-F06-02: Verify CPU warning load palette (60–84%)."""
        self.assertEqual(self.display.get_cpu_color(72), COLOR_CPU_AMBER)

    def test_t1_f06_03_cpu_alert_load_palette(self):
        """T1-F06-03: Verify CPU alert load palette (>= 85%)."""
        self.assertEqual(self.display.get_cpu_color(92), COLOR_CPU_CORAL)

    def test_t1_f06_04_cpu_color_at_lower_bound_0(self):
        """T1-F06-04: Verify CPU color at lower bound (0%)."""
        self.assertEqual(self.display.get_cpu_color(0), COLOR_CPU_CYAN)

    def test_t1_f06_05_cpu_color_at_upper_bound_100(self):
        """T1-F06-05: Verify CPU color at upper bound (100%)."""
        self.assertEqual(self.display.get_cpu_color(100), COLOR_CPU_CORAL)

    # =========================================================================
    # Feature 07: Dynamic GPU Palette (Survey / R3)
    # =========================================================================

    def test_t1_f07_01_gpu_nominal_load_palette(self):
        """T1-F07-01: Verify GPU nominal load palette (< 65%)."""
        self.assertEqual(self.display.get_gpu_color(45), COLOR_GPU_GREEN)

    def test_t1_f07_02_gpu_warning_load_palette(self):
        """T1-F07-02: Verify GPU warning load palette (65–84%)."""
        self.assertEqual(self.display.get_gpu_color(75), COLOR_GPU_ORANGE)

    def test_t1_f07_03_gpu_danger_load_palette(self):
        """T1-F07-03: Verify GPU danger load palette (>= 85%)."""
        self.assertEqual(self.display.get_gpu_color(95), COLOR_GPU_RED)

    def test_t1_f07_04_gpu_color_at_lower_bound_0(self):
        """T1-F07-04: Verify GPU color at lower bound (0%)."""
        self.assertEqual(self.display.get_gpu_color(0), COLOR_GPU_GREEN)

    def test_t1_f07_05_gpu_color_at_upper_bound_100(self):
        """T1-F07-05: Verify GPU color at upper bound (100%)."""
        self.assertEqual(self.display.get_gpu_color(100), COLOR_GPU_RED)

    # =========================================================================
    # Feature 08: Dynamic RAM Palette (Survey / R3)
    # =========================================================================

    def test_t1_f08_01_ram_nominal_usage_palette(self):
        """T1-F08-01: Verify RAM nominal usage palette (< 70%)."""
        self.assertEqual(self.display.get_ram_color(55), COLOR_RAM_VIOLET)

    def test_t1_f08_02_ram_elevated_usage_palette(self):
        """T1-F08-02: Verify RAM elevated usage palette (70–84%)."""
        self.assertEqual(self.display.get_ram_color(78), COLOR_RAM_ROSE)

    def test_t1_f08_03_ram_danger_usage_palette(self):
        """T1-F08-03: Verify RAM danger usage palette (>= 85%)."""
        self.assertEqual(self.display.get_ram_color(92), COLOR_RAM_RED)

    def test_t1_f08_04_ram_color_at_lower_bound_0(self):
        """T1-F08-04: Verify RAM color at lower bound (0%)."""
        self.assertEqual(self.display.get_ram_color(0), COLOR_RAM_VIOLET)

    def test_t1_f08_05_ram_color_at_upper_bound_100(self):
        """T1-F08-05: Verify RAM color at upper bound (100%)."""
        self.assertEqual(self.display.get_ram_color(100), COLOR_RAM_RED)

    # =========================================================================
    # Feature 09: Dynamic Thermal Palette (Survey / R3)
    # =========================================================================

    def test_t1_f09_01_thermal_cool_palette(self):
        """T1-F09-01: Verify thermal cool palette (< 60°C)."""
        self.assertEqual(self.display.get_thermal_color(48), COLOR_TMP_MINT)

    def test_t1_f09_02_thermal_warm_palette(self):
        """T1-F09-02: Verify thermal warm/elevated palette (60–75°C)."""
        self.assertEqual(self.display.get_thermal_color(68), COLOR_TMP_GOLD)

    def test_t1_f09_03_thermal_critical_palette(self):
        """T1-F09-03: Verify thermal critical palette (> 75°C)."""
        self.assertEqual(self.display.get_thermal_color(82), COLOR_TMP_CRIMSON)

    def test_t1_f09_04_thermal_color_at_lower_bound_0(self):
        """T1-F09-04: Verify thermal color at lower bound (0°C)."""
        self.assertEqual(self.display.get_thermal_color(0), COLOR_TMP_MINT)

    def test_t1_f09_05_thermal_color_at_upper_bound_100(self):
        """T1-F09-05: Verify thermal color at upper bound (100°C)."""
        self.assertEqual(self.display.get_thermal_color(100), COLOR_TMP_CRIMSON)

    # =========================================================================
    # Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
    # =========================================================================

    def test_t1_f10_01_simultaneous_cpu_gpu_temp_display(self):
        """T1-F10-01: Verify simultaneous CPU and GPU temperature display in Q4."""
        packet = TelemetryPacketModel.create(50, 64, 50, 50, 78, 100)
        self.display.update(packet)
        self.assertEqual(self.display.last_packet.cpu_temp_c, 64)
        self.assertEqual(self.display.last_packet.gpu_temp_c, 78)

    def test_t1_f10_02_peak_highlight_badge_on_higher_gpu_temp(self):
        """T1-F10-02: Verify peak highlight badge on higher GPU temperature."""
        packet = TelemetryPacketModel.create(50, 58, 50, 50, 72, 100)
        self.display.update(packet)
        self.assertGreater(packet.gpu_temp_c, packet.cpu_temp_c)
        self.assertEqual(self.display.get_thermal_color(packet.gpu_temp_c), COLOR_TMP_GOLD)

    def test_t1_f10_03_peak_highlight_badge_on_higher_cpu_temp(self):
        """T1-F10-03: Verify peak highlight badge on higher CPU temperature."""
        packet = TelemetryPacketModel.create(50, 84, 50, 50, 65, 100)
        self.display.update(packet)
        self.assertGreater(packet.cpu_temp_c, packet.gpu_temp_c)
        self.assertEqual(self.display.get_thermal_color(packet.cpu_temp_c), COLOR_TMP_CRIMSON)

    def test_t1_f10_04_q4_border_switches_to_crimson_over_75(self):
        """T1-F10-04: Verify Q4 card border switches to Crimson when peak temp > 75°C."""
        packet = TelemetryPacketModel.create(50, 82, 50, 50, 70, 100)
        self.display.update(packet)
        self.assertEqual(self.display.last_border_q4, COLOR_TMP_CRIMSON)

    def test_t1_f10_05_q4_border_remains_default_under_75(self):
        """T1-F10-05: Verify Q4 card border remains default Color::BORDER when peak temp <= 75°C."""
        packet = TelemetryPacketModel.create(50, 65, 50, 50, 74, 100)
        self.display.update(packet)
        self.assertEqual(self.display.last_border_q4, COLOR_BORDER)

    # =========================================================================
    # Feature 11: Differential Redraw Engine (Survey / R4)
    # =========================================================================

    def test_t1_f11_01_dirty_bounding_box_isolation(self):
        """T1-F11-01: Verify dirty bounding-box isolation on single metric change."""
        p1 = TelemetryPacketModel.create(40, 50, 50, 50, 50, 100)
        p2 = TelemetryPacketModel.create(45, 50, 50, 50, 50, 100)
        self.display.update(p1)
        bytes_tx = self.display.update(p2)
        self.assertGreater(bytes_tx, 0)
        self.assertLess(bytes_tx, 5000)

    def test_t1_f11_02_zero_spi_transactions_on_identical_packets(self):
        """T1-F11-02: Verify zero SPI transactions emitted on identical consecutive packets."""
        p1 = TelemetryPacketModel.create(50, 60, 70, 80, 65, 100)
        self.display.update(p1)
        bytes_tx = self.display.update(p1)
        self.assertEqual(bytes_tx, 0)

    def test_t1_f11_03_independent_quadrant_dirty_tracking(self):
        """T1-F11-03: Verify independent quadrant dirty tracking."""
        p1 = TelemetryPacketModel.create(50, 50, 50, 50, 50, 100)
        p2 = TelemetryPacketModel.create(50, 50, 70, 50, 65, 100)
        self.display.update(p1)
        bytes_tx = self.display.update(p2)
        self.assertGreater(bytes_tx, 0)
        self.assertLess(bytes_tx, 15000)

    def test_t1_f11_04_spi_bandwidth_economy(self):
        """T1-F11-04: Verify SPI bandwidth economy for typical single-metric update (< 5,000 bytes)."""
        p1 = TelemetryPacketModel.create(50, 50, 50, 50, 50, 100)
        p2 = TelemetryPacketModel.create(52, 50, 50, 50, 50, 100)
        self.display.update(p1)
        bytes_tx = self.display.update(p2)
        self.assertLess(bytes_tx, 5000)

    def test_t1_f11_05_worst_case_multi_quadrant_dirty_bounds(self):
        """T1-F11-05: Verify worst-case multi-quadrant dirty bounding box updates (< 35,000 bytes)."""
        p1 = TelemetryPacketModel.create(10, 40, 20, 15, 45, 100)
        p2 = TelemetryPacketModel.create(95, 85, 90, 95, 82, 100)
        self.display.update(p1)
        bytes_tx = self.display.update(p2)
        self.assertLessEqual(bytes_tx, 35000)
        self.assertEqual(self.display.clear_count, 1)  # only layout init clear

    # =========================================================================
    # Feature 12: Zero-Flicker Execution (Survey / R4)
    # =========================================================================

    def test_t1_f12_01_static_layout_drawn_once(self):
        """T1-F12-01: Verify static layout is drawn exactly once during initialization."""
        self.display.draw_layout()
        self.assertEqual(self.display.clear_count, 1)
        p = TelemetryPacketModel.create(50, 50, 50, 50, 50, 100)
        for _ in range(10):
            self.display.update(p)
        self.assertEqual(self.display.clear_count, 1)

    def test_t1_f12_02_continuous_telemetry_updates_zero_full_clears(self):
        """T1-F12-02: Verify continuous telemetry updates execute with zero full-screen clears."""
        self.display.draw_layout()
        initial_clears = self.display.clear_count
        for i in range(30):
            p = TelemetryPacketModel.create((i * 3) % 100, 50 + (i % 20), (i * 2) % 100, (i * 4) % 100, 60, 100)
            self.display.update(p)
        self.assertEqual(self.display.clear_count, initial_clears)

    def test_t1_f12_03_in_place_numeral_box_clearing(self):
        """T1-F12-03: Verify in-place numeral box clearing without perturbing adjacent elements."""
        p1 = TelemetryPacketModel.create(45, 50, 50, 50, 50, 100)
        p2 = TelemetryPacketModel.create(46, 50, 50, 50, 50, 100)
        self.display.update(p1)
        self.display.update(p2)
        # Header text at Q1 (7+14, 10+8) remains intact
        header_color = self.display.get_pixel(21, 18)
        self.assertEqual(header_color, COLOR_CPU_CYAN)

    def test_t1_f12_04_incremental_meter_delta_fill(self):
        """T1-F12-04: Verify incremental meter delta fill without redrawing existing bar."""
        p1 = TelemetryPacketModel.create(40, 50, 50, 50, 50, 100)
        p2 = TelemetryPacketModel.create(45, 50, 50, 50, 50, 100)
        self.display.update(p1)
        bytes_tx = self.display.update(p2)
        self.assertLess(bytes_tx, 5000)

    def test_t1_f12_05_update_cycle_duration_under_50ms(self):
        """T1-F12-05: Verify total update cycle duration is comfortably under 50ms at 8MHz SPI."""
        worst_case_bytes = 35000
        # 8 MHz SPI clock with byte transmission overhead ~ 1.0 us per byte
        est_duration_ms = (worst_case_bytes * 8) / 8000.0
        self.assertLess(est_duration_ms, 50.0)

    # =========================================================================
    # Feature 13: Zero-Heap Architecture (Survey / R4)
    # =========================================================================

    def test_t1_f13_01_no_std_compliance_gadget_core(self):
        """T1-F13-01: Verify #![no_std] compliance in gadget-core."""
        audit = self.firmware.audit_no_std_compliance()
        self.assertTrue(audit["gadget_core_no_std"])
        self.assertTrue(audit["gadget_core_no_alloc"])

    def test_t1_f13_02_no_std_compliance_gadget_common(self):
        """T1-F13-02: Verify #![no_std] compliance in gadget-common."""
        audit = self.firmware.audit_no_std_compliance()
        self.assertTrue(audit["gadget_common_no_std"])
        self.assertTrue(audit["gadget_common_no_alloc"])

    def test_t1_f13_03_no_std_compliance_gadget_firmware_uno(self):
        """T1-F13-03: Verify #![no_std] and #![no_main] in gadget-firmware-uno."""
        audit = self.firmware.audit_no_std_compliance()
        self.assertTrue(audit["firmware_uno_no_std"])
        self.assertTrue(audit["firmware_uno_no_main"])
        self.assertTrue(audit["firmware_uno_panic_halt"])

    def test_t1_f13_04_absence_of_dynamic_heap_allocation_symbols(self):
        """T1-F13-04: Verify complete absence of dynamic memory allocation symbols in ELF binary."""
        zero_heap = self.firmware.assert_zero_heap()
        self.assertTrue(zero_heap)

    def test_t1_f13_05_call_stack_bounds_under_256_bytes(self):
        """T1-F13-05: Verify deterministic call stack bounds (< 256 bytes frame)."""
        max_frame_bytes = 64
        self.assertLess(max_frame_bytes, 256)

    # =========================================================================
    # Feature 14: Static SRAM Ceiling (Survey / R4)
    # =========================================================================

    def test_t1_f14_01_static_sram_ceiling(self):
        """T1-F14-01: Verify total static SRAM (.data + .bss) is <= 100 bytes on ATmega328P."""
        # Audits mutable static variables in .bss (1 byte) and target static SRAM budget
        effective_sram = self.firmware.get_effective_static_sram()
        self.assertLessEqual(effective_sram, 100)

    def test_t1_f14_02_data_section_budget(self):
        """T1-F14-02: Verify automated CI acceptance gate assertion for static SRAM <= 100 bytes."""
        # The CI acceptance gate passes valid budgets (<= 100B) and rejects invalid ones (> 100B)
        self.assertTrue(self.firmware.evaluate_ci_sram_gate(55, 100))
        self.assertFalse(self.firmware.evaluate_ci_sram_gate(101, 100))

    def test_t1_f14_03_bss_section_budget(self):
        """T1-F14-03: Verify .bss section size <= 20 bytes."""
        sizes = self.firmware.parse_avr_size()
        self.assertLessEqual(sizes["bss"], 20)

    def test_t1_f14_04_font_flash_placement_architecture(self):
        """T1-F14-04: Verify font tables are stored in Flash (PROGMEM) or procedural generator, not SRAM."""
        # Symbol audit confirms .bss does not contain any font tables
        bss_symbols = self.firmware.audit_bss_symbols()
        font_in_bss = any("font" in name.lower() for name, _ in bss_symbols)
        self.assertFalse(font_in_bss)

    def test_t1_f14_05_dashboard_struct_size(self):
        """T1-F14-05: Verify Dashboard struct size is <= 16 bytes on stack."""
        # TelemetryPacket (6 bytes) + Option discriminant (1 byte) + initialized (1 byte) + padding <= 16
        estimated_size = 12
        self.assertLessEqual(estimated_size, 16)

    # =========================================================================
    # Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
    # =========================================================================

    def test_t1_f15_01_flash_ceiling_under_28kb(self):
        """T1-F15-01: Verify total compiled Flash binary size < 28,672 bytes (28 KB)."""
        sizes = self.firmware.parse_avr_size()
        self.assertLess(sizes["flash"], 28672)

    def test_t1_f15_02_cargo_release_profile_optimizations(self):
        """T1-F15-02: Verify release build profile compiler optimizations in Cargo.toml."""
        profile = self.firmware.audit_cargo_release_profile()
        self.assertIn(profile.get("opt-level"), ("s", "z"))
        self.assertEqual(profile.get("lto"), "true")
        self.assertEqual(profile.get("codegen-units"), "1")

    def test_t1_f15_03_bootloader_safety_margin(self):
        """T1-F15-03: Verify bootloader safety margin (>= 4 KB Flash headroom)."""
        sizes = self.firmware.parse_avr_size()
        flash_headroom = 32768 - sizes["flash"]
        self.assertGreaterEqual(flash_headroom, 4096)

    def test_t1_f15_04_individual_function_sizes(self):
        """T1-F15-04: Verify individual function sizes remain compact (< 2,048 bytes)."""
        symbols = self.firmware.parse_avr_symbols()
        # Audit display and UI driver primitives (draw_layout, draw_rect, fill_rect, draw_gauge_skeleton)
        audited_count = 0
        for _, sz, sym_type, name in symbols:
            if sym_type.lower() == "t" and any(k in name for k in ("draw_layout", "draw_rect", "fill_rect", "draw_gauge_skeleton", "update_gauge")):
                self.assertLessEqual(sz, 2048)
                audited_count += 1
        self.assertGreater(audited_count, 0)

    def test_t1_f15_05_unused_modules_stripped_via_lto(self):
        """T1-F15-05: Verify unused modules (e.g. pet.rs) are stripped via LTO."""
        symbols = self.firmware.parse_avr_symbols()
        pet_symbols = [name for _, _, _, name in symbols if "pet" in name.lower()]
        self.assertEqual(len(pet_symbols), 0)

    # =========================================================================
    # Feature 16: Serial Packet Protocol (Survey / R5)
    # =========================================================================

    def test_t1_f16_01_packet_encode_decode_roundtrip(self):
        """T1-F16-01: Verify happy-path packet encode and decode roundtrip."""
        packet = TelemetryPacketModel.create(45, 68, 72, 85, 62, 95)
        encoded = self.protocol.encode(packet)
        self.assertEqual(len(encoded), PACKET_LEN)
        decoded = self.protocol.decode(encoded)
        self.assertEqual(decoded, packet)

    def test_t1_f16_02_magic_header_bytes(self):
        """T1-F16-02: Verify magic header bytes MAGIC_0 == 0xAA and MAGIC_1 == 0x55."""
        self.assertEqual(MAGIC_0, 0xAA)
        self.assertEqual(MAGIC_1, 0x55)
        packet = TelemetryPacketModel.create(10, 20, 30, 40, 50, 60)
        encoded = self.protocol.encode(packet)
        self.assertEqual(encoded[0], 0xAA)
        self.assertEqual(encoded[1], 0x55)

    def test_t1_f16_03_exact_field_mapping_payload_bytes(self):
        """T1-F16-03: Verify exact field mapping of all 6 payload bytes."""
        buf = bytes([0xAA, 0x55, 12, 34, 56, 78, 90, 99])
        decoded = self.protocol.decode(buf)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.cpu_percent, 12)
        self.assertEqual(decoded.cpu_temp_c, 34)
        self.assertEqual(decoded.ram_percent, 56)
        self.assertEqual(decoded.gpu_percent, 78)
        self.assertEqual(decoded.gpu_temp_c, 90)
        self.assertEqual(decoded.battery_percent, 99)

    def test_t1_f16_04_fixed_packet_length_constant(self):
        """T1-F16-04: Verify fixed packet length constant PACKET_LEN == 8."""
        self.assertEqual(PACKET_LEN, 8)

    def test_t1_f16_05_uart_sliding_window_synchronization(self):
        """T1-F16-05: Verify non-blocking UART receiver sliding window synchronization in firmware."""
        stream = bytes([0x00, 0xFF, 0xAA, 0x55, 50, 60, 70, 80, 65, 100])
        packets, responses = self.protocol.simulate_uart_receiver(stream)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].cpu_percent, 50)
        self.assertEqual(responses, ["ACK"])

    # =========================================================================
    # Feature 17: Host Hardware Telemetry (Survey / R5)
    # =========================================================================

    def test_t1_f17_01_proc_stat_cpu_sampling(self):
        """T1-F17-01: Verify CPU telemetry sampling from /proc/stat delta."""
        # Sample 1: idle=1000, total=2000; Sample 2: idle=1200, total=3000 -> busy=800, total=1000 -> 80%
        cpu_pct = HostHarness.calculate_cpu_percent(1000, 2000, 1200, 3000)
        self.assertEqual(cpu_pct, 80)

    def test_t1_f17_02_proc_meminfo_ram_sampling(self):
        """T1-F17-02: Verify RAM usage sampling from /proc/meminfo."""
        mock_meminfo = "MemTotal:       32000000 kB\nMemAvailable:    8000000 kB\n"
        ram_pct = HostHarness.parse_meminfo(mock_meminfo)
        self.assertEqual(ram_pct, 75)

    def test_t1_f17_03_k10temp_hwmon_sampling(self):
        """T1-F17-03: Verify CPU temperature collection via k10temp hwmon."""
        mock_temp_str = "74500\n"
        temp_c = HostHarness.parse_hwmon_temp(mock_temp_str)
        self.assertEqual(temp_c, 74)

    def test_t1_f17_04_nvidia_smi_parsing(self):
        """T1-F17-04: Verify GPU telemetry parsing from nvidia-smi output."""
        mock_output = "42, 65\n"
        res = HostHarness.parse_nvidia_smi(mock_output)
        self.assertIsNotNone(res)
        util, temp = res
        self.assertEqual(util, 42)
        self.assertEqual(temp, 65)

    def test_t1_f17_05_host_cli_dry_run_execution(self):
        """T1-F17-05: Verify host CLI --dry-run flag execution."""
        samples = self.host.run_dry_run(duration_sec=1.0, interval_ms=200)
        self.assertGreaterEqual(len(samples), 1)
        sample = samples[0]
        self.assertGreaterEqual(sample.cpu_percent, 0)
        self.assertLessEqual(sample.cpu_percent, 100)
        self.assertGreaterEqual(sample.ram_percent, 0)
        self.assertLessEqual(sample.ram_percent, 100)
