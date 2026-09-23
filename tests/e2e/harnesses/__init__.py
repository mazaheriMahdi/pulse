"""
Desktop Performance Monitor E2E Test Harnesses Package
Provides opaque-box test harnesses for host daemon, wire protocol,
headless display simulation, and firmware resource ceiling analysis.
"""
from .host_harness import HostHarness, TelemetrySample
from .protocol_harness import ProtocolHarness, TelemetryPacketModel
from .display_harness import (
    DisplayHarness,
    Color,
    CARD_BOUNDS,
    HEADER_LABELS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from .firmware_harness import FirmwareHarness

__all__ = [
    "HostHarness",
    "TelemetrySample",
    "ProtocolHarness",
    "TelemetryPacketModel",
    "DisplayHarness",
    "Color",
    "CARD_BOUNDS",
    "HEADER_LABELS",
    "SCREEN_WIDTH",
    "SCREEN_HEIGHT",
    "FirmwareHarness",
]
