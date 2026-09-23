"""
Headless MIPI DCS Display Driver & 480x320 Framebuffer Simulator
Models the ILI9488 display, 4-Quadrant card grid layout, typography,
chunky meters, dynamic palettes, and differential redraw engine.
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .protocol_harness import TelemetryPacketModel

SCREEN_WIDTH: int = 480
SCREEN_HEIGHT: int = 320

CARD_WIDTH: int = 230
CARD_HEIGHT: int = 145

X_MARGIN: int = 7
Y_MARGIN: int = 10
X_GAP: int = 6
Y_GAP: int = 10

CARD_BOUNDS: Dict[str, Tuple[int, int, int, int]] = {
    "Q1": (X_MARGIN, Y_MARGIN, CARD_WIDTH, CARD_HEIGHT),  # (7, 10, 230, 145) -> X: 7..236, Y: 10..154
    "Q2": (X_MARGIN + CARD_WIDTH + X_GAP, Y_MARGIN, CARD_WIDTH, CARD_HEIGHT),  # (243, 10, 230, 145) -> X: 243..472
    "Q3": (X_MARGIN, Y_MARGIN + CARD_HEIGHT + Y_GAP, CARD_WIDTH, CARD_HEIGHT),  # (7, 165, 230, 145) -> Y: 165..309
    "Q4": (X_MARGIN + CARD_WIDTH + X_GAP, Y_MARGIN + CARD_HEIGHT + Y_GAP, CARD_WIDTH, CARD_HEIGHT),  # (243, 165)
}

HEADER_LABELS: Dict[str, str] = {
    "Q1": "CPU LOAD",
    "Q2": "GPU LOAD",
    "Q3": "RAM USAGE",
    "Q4": "THERMALS",
}


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    def as_rgb_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def luminance(self) -> float:
        """Computes relative luminance per sRGB / WCAG specification."""
        def channel_lum(c: int) -> float:
            c_norm = c / 255.0
            return c_norm / 12.92 if c_norm <= 0.03928 else ((c_norm + 0.055) / 1.055) ** 2.4

        return 0.2126 * channel_lum(self.r) + 0.7152 * channel_lum(self.g) + 0.0722 * channel_lum(self.b)

    def contrast_ratio(self, other: "Color") -> float:
        """Computes WCAG luminance contrast ratio (1.0 to 21.0)."""
        l1 = self.luminance()
        l2 = other.luminance()
        brightest = max(l1, l2)
        darkest = min(l1, l2)
        return (brightest + 0.05) / (darkest + 0.05)

    def distance_to(self, other: "Color") -> float:
        """Euclidean distance in RGB space."""
        return math.sqrt((self.r - other.r) ** 2 + (self.g - other.g) ** 2 + (self.b - other.b) ** 2)


# Palette Constants
COLOR_BLACK = Color(0, 0, 0)
COLOR_WHITE = Color(255, 255, 255)
COLOR_DARK_BG = Color(18, 22, 34)       # Screen Background (#121622)
COLOR_PANEL_BG = Color(28, 34, 52)      # Card Interior (#1C2234)
COLOR_BORDER = Color(50, 62, 90)        # Default Card Border (#323E5A)
COLOR_TEXT_MUTED = Color(130, 145, 175) # Muted Text / Non-Peak (#8291AF)

# CPU Palette
COLOR_CPU_CYAN = Color(0, 210, 211)     # Electric Cyan (#00D2D3) < 60%
COLOR_CPU_AMBER = Color(255, 165, 2)    # Coral Amber (#FFA502) 60-84%
COLOR_CPU_CORAL = Color(255, 107, 107)  # Alert Coral (#FF6B6B) >= 85%

# GPU Palette
COLOR_GPU_GREEN = Color(16, 172, 132)   # Neon Green (#10AC84) < 65%
COLOR_GPU_ORANGE = Color(255, 159, 67)  # Warning Orange (#FF9F43) 65-84%
COLOR_GPU_RED = Color(255, 56, 56)      # Blaze Red (#FF3838) >= 85%

# RAM Palette
COLOR_RAM_VIOLET = Color(165, 94, 234)  # Vivid Violet (#A55EEA) < 70%
COLOR_RAM_ROSE = Color(217, 128, 250)   # Magenta Rose (#D980FA) 70-84%
COLOR_RAM_RED = Color(234, 32, 39)      # Danger Red (#EA2027) >= 85%

# Thermal Palette
COLOR_TMP_MINT = Color(29, 209, 161)    # Cool Mint (#1DD1A1) < 60°C
COLOR_TMP_GOLD = Color(254, 202, 87)    # Gold (#FECA57) 60-75°C
COLOR_TMP_CRIMSON = Color(255, 56, 56)  # Crimson (#FF3838) > 75°C


@dataclass
class SpiTransaction:
    cmd: int
    window: Optional[Tuple[int, int, int, int]] = None  # (x0, y0, x1, y1)
    bytes_transferred: int = 0


class DisplayHarness:
    """
    Headless MIPI DCS virtual display and differential redraw simulation harness.
    """

    def __init__(self):
        self.framebuffer: List[List[Color]] = [
            [COLOR_BLACK for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)
        ]
        self.transactions: List[SpiTransaction] = []
        self.clear_count: int = 0
        self.last_packet: Optional[TelemetryPacketModel] = None
        self.last_border_q4: Color = COLOR_BORDER
        self.initialized: bool = False

    def clear(self, color: Color = COLOR_DARK_BG):
        """Simulates full screen clear over SPI."""
        self.clear_count += 1
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                self.framebuffer[y][x] = color
        # Full screen clear: 480 * 320 * 3 bytes
        self.transactions.append(
            SpiTransaction(cmd=0x2C, window=(0, 0, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1), bytes_transferred=SCREEN_WIDTH * SCREEN_HEIGHT * 3)
        )

    def fill_rect(self, x: int, y: int, w: int, h: int, color: Color):
        """Fills a solid rectangle within bounds, recording SPI window transaction."""
        x0 = max(0, min(SCREEN_WIDTH - 1, x))
        y0 = max(0, min(SCREEN_HEIGHT - 1, y))
        x1 = max(0, min(SCREEN_WIDTH - 1, x + w - 1))
        y1 = max(0, min(SCREEN_HEIGHT - 1, y + h - 1))

        if x1 < x0 or y1 < y0:
            return

        for py in range(y0, y1 + 1):
            for px in range(x0, x1 + 1):
                self.framebuffer[py][px] = color

        bytes_written = (x1 - x0 + 1) * (y1 - y0 + 1) * 3
        self.transactions.append(
            SpiTransaction(cmd=0x2C, window=(x0, y0, x1, y1), bytes_transferred=bytes_written)
        )

    def draw_rect(self, x: int, y: int, w: int, h: int, color: Color):
        """Outlines a 1px rectangle."""
        self.fill_rect(x, y, w, 1, color)
        self.fill_rect(x, y + h - 1, w, 1, color)
        self.fill_rect(x, y, 1, h, color)
        self.fill_rect(x + w - 1, y, 1, h, color)

    def draw_thick_rect(self, x: int, y: int, w: int, h: int, thickness: int, color: Color):
        """Outlines a border of given thickness."""
        for t in range(thickness):
            self.draw_rect(x + t, y + t, w - 2 * t, h - 2 * t, color)

    def get_pixel(self, x: int, y: int) -> Color:
        """Inspects pixel color at (x, y)."""
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            return self.framebuffer[y][x]
        return COLOR_BLACK

    # --- 4-Quadrant UI Layout Simulation ---

    def draw_layout(self):
        """Renders static 4-quadrant layout once on startup."""
        self.clear(COLOR_DARK_BG)

        for q_name, (qx, qy, qw, qh) in CARD_BOUNDS.items():
            # Card panel interior
            self.fill_rect(qx, qy, qw, qh, COLOR_PANEL_BG)
            # 2px border
            self.draw_thick_rect(qx, qy, qw, qh, 2, COLOR_BORDER)

            # Header text region (14px high, scale 2)
            header_color = self.get_header_accent_color(q_name)
            self.fill_rect(qx + 14, qy + 8, 100, 14, header_color)

            # Empty chunky meter track (202x24 outer, 200x22 inner)
            if q_name != "Q4":  # Q1, Q2, Q3 have standard meters
                self.draw_rect(qx + 14, qy + 70, 202, 24, COLOR_BORDER)
                self.fill_rect(qx + 15, qy + 71, 200, 22, COLOR_DARK_BG)
            else:
                # Q4 Thermals track / info box
                self.draw_rect(qx + 14, qy + 70, 202, 24, COLOR_BORDER)
                self.fill_rect(qx + 15, qy + 71, 200, 22, COLOR_DARK_BG)

        self.initialized = True
        self.last_border_q4 = COLOR_BORDER

    @staticmethod
    def get_header_accent_color(q_name: str) -> Color:
        """Returns header title accent color for quadrant."""
        if q_name == "Q1":
            return COLOR_CPU_CYAN
        elif q_name == "Q2":
            return COLOR_GPU_GREEN
        elif q_name == "Q3":
            return COLOR_RAM_VIOLET
        elif q_name == "Q4":
            return COLOR_TMP_MINT
        return COLOR_WHITE

    @staticmethod
    def get_cpu_color(val: int) -> Color:
        """Dynamic CPU Palette: Cyan (<60%) -> Amber (60-84%) -> Coral (>=85%)."""
        if val < 60:
            return COLOR_CPU_CYAN
        elif val < 85:
            return COLOR_CPU_AMBER
        return COLOR_CPU_CORAL

    @staticmethod
    def get_gpu_color(val: int) -> Color:
        """Dynamic GPU Palette: Green (<65%) -> Orange (65-84%) -> Blaze Red (>=85%)."""
        if val < 65:
            return COLOR_GPU_GREEN
        elif val < 85:
            return COLOR_GPU_ORANGE
        return COLOR_GPU_RED

    @staticmethod
    def get_ram_color(val: int) -> Color:
        """Dynamic RAM Palette: Violet (<70%) -> Magenta (70-84%) -> Danger Red (>=85%)."""
        if val < 70:
            return COLOR_RAM_VIOLET
        elif val < 85:
            return COLOR_RAM_ROSE
        return COLOR_RAM_RED

    @staticmethod
    def get_thermal_color(temp_c: int) -> Color:
        """Dynamic Thermal Palette: Mint (<60°C) -> Gold (60-75°C) -> Crimson (>75°C)."""
        if temp_c < 60:
            return COLOR_TMP_MINT
        elif temp_c <= 75:
            return COLOR_TMP_GOLD
        return COLOR_TMP_CRIMSON

    # --- Differential Update Engine ---

    def update(self, packet: TelemetryPacketModel) -> int:
        """
        Executes differential update for new packet with zero full screen clears.
        Returns total SPI bytes transferred during this update.
        """
        if not self.initialized:
            self.draw_layout()

        last = self.last_packet
        if last is not None and last == packet:
            # 0 delta -> 0 SPI transactions emitted!
            return 0

        start_tx_idx = len(self.transactions)

        # Q1 CPU
        if last is None or last.cpu_percent != packet.cpu_percent:
            self._update_quadrant_metric("Q1", packet.cpu_percent, "%", self.get_cpu_color(packet.cpu_percent))

        # Q2 GPU
        if last is None or last.gpu_percent != packet.gpu_percent:
            self._update_quadrant_metric("Q2", packet.gpu_percent, "%", self.get_gpu_color(packet.gpu_percent))

        # Q3 RAM
        if last is None or last.ram_percent != packet.ram_percent:
            self._update_quadrant_metric("Q3", packet.ram_percent, "%", self.get_ram_color(packet.ram_percent))

        # Q4 Thermals (CPU temp & GPU temp)
        if last is None or last.cpu_temp_c != packet.cpu_temp_c or last.gpu_temp_c != packet.gpu_temp_c:
            self._update_thermal_quadrant(packet.cpu_temp_c, packet.gpu_temp_c)

        self.last_packet = packet

        # Sum SPI bytes written during this update
        bytes_transferred = sum(tx.bytes_transferred for tx in self.transactions[start_tx_idx:])
        return bytes_transferred

    def _update_quadrant_metric(self, q_name: str, value: int, suffix: str, color: Color):
        """Updates numeral box and chunky meter track for a quadrant using differential deltas."""
        qx, qy, qw, qh = CARD_BOUNDS[q_name]
        val_clamped = min(100, max(0, value))

        last_val = None
        last_color = None
        if self.last_packet is not None:
            if q_name == "Q1":
                last_val = self.last_packet.cpu_percent
                last_color = self.get_cpu_color(last_val)
            elif q_name == "Q2":
                last_val = self.last_packet.gpu_percent
                last_color = self.get_gpu_color(last_val)
            elif q_name == "Q3":
                last_val = self.last_packet.ram_percent
                last_color = self.get_ram_color(last_val)

        # 1. Numeral box single-pass update (direct glyph render with fg/bg):
        num_x = qx + 14
        num_y = qy + 26
        if last_val is None or abs(val_clamped - last_val) > 5 or (val_clamped == 100 or last_val == 100):
            # 3-digit / large delta numeral update (single-pass ~35x24)
            self.fill_rect(num_x, num_y, 35, 24, color)
        else:
            # Incremental single digit delta update (~15x24)
            self.fill_rect(num_x + 20, num_y, 15, 24, color)

        # 2. Chunky meter delta update:
        meter_x = qx + 15
        meter_y = qy + 71
        fill_w = val_clamped * 2
        fill_h = 10

        if last_val is None or (last_color is not None and last_color != color):
            # Threshold crossed: recolor active bar directly
            if fill_w > 0:
                self.fill_rect(meter_x, meter_y, fill_w, fill_h, color)
        else:
            prev_fill_w = last_val * 2
            if fill_w > prev_fill_w:
                # Incremental fill delta only!
                delta_w = fill_w - prev_fill_w
                self.fill_rect(meter_x + prev_fill_w, meter_y, delta_w, fill_h, color)
            elif fill_w < prev_fill_w:
                # Decremental clear delta only!
                delta_w = prev_fill_w - fill_w
                self.fill_rect(meter_x + fill_w, meter_y, delta_w, fill_h, COLOR_DARK_BG)

    def _update_thermal_quadrant(self, cpu_temp: int, gpu_temp: int):
        """Updates dual temperature readouts, peak highlight badge, and card border in Q4."""
        qx, qy, qw, qh = CARD_BOUNDS["Q4"]
        peak_temp = max(cpu_temp, gpu_temp)

        cpu_color = self.get_thermal_color(cpu_temp)
        gpu_color = self.get_thermal_color(gpu_temp)

        # Single-pass render for dual readouts
        self.fill_rect(qx + 14, qy + 26, 25, 28, cpu_color)
        self.fill_rect(qx + 50, qy + 26, 25, 28, gpu_color)

        # Dynamic card border shift if peak > 75°C
        target_border = COLOR_TMP_CRIMSON if peak_temp > 75 else COLOR_BORDER
        if target_border != self.last_border_q4:
            self.draw_thick_rect(qx, qy, qw, qh, 2, target_border)
            self.last_border_q4 = target_border

    # --- Ergonomic & Optical Calculations ---

    @staticmethod
    def calculate_visual_angle_arcmin(pixel_height: int, viewing_distance_mm: float, dpi: float = 166.0) -> float:
        """
        Calculates subtended optical visual angle in arcminutes per ISO 9241-303.
        formula: theta = 2 * arctan(h_mm / (2 * distance_mm)) * (180 * 60 / pi)
        """
        pixel_pitch_mm = 25.4 / dpi  # approx 0.153 mm/pixel
        physical_height_mm = pixel_height * pixel_pitch_mm
        angle_rad = 2.0 * math.atan(physical_height_mm / (2.0 * viewing_distance_mm))
        return angle_rad * (180.0 * 60.0 / math.pi)
