"""
Wire Protocol & UART Framing Harness
Tests binary packet encoding/decoding and models the ATmega328P
UART sliding window receiver state machine.
"""
import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple

MAGIC_0: int = 0xAA
MAGIC_1: int = 0x55
PACKET_LEN: int = 8


@dataclass(frozen=True)
class TelemetryPacketModel:
    cpu_percent: int
    cpu_temp_c: int
    ram_percent: int
    gpu_percent: int
    gpu_temp_c: int
    battery_percent: int

    @classmethod
    def create(
        cls,
        cpu: int,
        cpu_temp: int,
        ram: int,
        gpu: int,
        gpu_temp: int,
        battery: int,
    ) -> "TelemetryPacketModel":
        """
        Creates a TelemetryPacketModel enforcing percentage clamping (0..100)
        while preserving temperature values (0..255).
        Matches TelemetryPacket::new in software/gadget-common/src/lib.rs.
        """
        return cls(
            cpu_percent=min(100, max(0, cpu)),
            cpu_temp_c=max(0, min(255, cpu_temp)),
            ram_percent=min(100, max(0, ram)),
            gpu_percent=min(100, max(0, gpu)),
            gpu_temp_c=max(0, min(255, gpu_temp)),
            battery_percent=min(100, max(0, battery)),
        )


class ProtocolHarness:
    """Harness for encoding, decoding, and validating wire protocol frames."""

    MAGIC_0 = MAGIC_0
    MAGIC_1 = MAGIC_1
    PACKET_LEN = PACKET_LEN

    @staticmethod
    def encode(packet: TelemetryPacketModel) -> bytes:
        """
        Serializes packet to 8-byte frame:
        [MAGIC_0, MAGIC_1, cpu, cpu_temp, ram, gpu, gpu_temp, battery]
        """
        return struct.pack(
            "BBBBBBBB",
            MAGIC_0,
            MAGIC_1,
            packet.cpu_percent,
            packet.cpu_temp_c,
            packet.ram_percent,
            packet.gpu_percent,
            packet.gpu_temp_c,
            packet.battery_percent,
        )

    @staticmethod
    def decode(buf: bytes) -> Optional[TelemetryPacketModel]:
        """
        Deserializes an 8-byte frame.
        Returns None if buffer is < 8 bytes or header != 0xAA 0x55.
        """
        if len(buf) < PACKET_LEN:
            return None
        if buf[0] != MAGIC_0 or buf[1] != MAGIC_1:
            return None

        return TelemetryPacketModel.create(
            cpu=buf[2],
            cpu_temp=buf[3],
            ram=buf[4],
            gpu=buf[5],
            gpu_temp=buf[6],
            battery=buf[7],
        )

    @staticmethod
    def simulate_uart_receiver(stream: bytes) -> Tuple[List[TelemetryPacketModel], List[str]]:
        """
        Exact simulation of the firmware UART sliding window state machine from
        software/gadget-firmware-uno/src/main.rs:90-130.
        Returns (list_of_decoded_packets, list_of_emitted_responses).
        """
        rx_buf = [0] * PACKET_LEN
        rx_idx = 0
        decoded_packets: List[TelemetryPacketModel] = []
        emitted_responses: List[str] = []

        for b in stream:
            if rx_idx == 0:
                if b == MAGIC_0:
                    rx_buf[0] = b
                    rx_idx = 1
            elif rx_idx == 1:
                if b == MAGIC_1:
                    rx_buf[1] = b
                    rx_idx = 2
                elif b == MAGIC_0:
                    rx_idx = 1
                else:
                    rx_idx = 0
            else:
                rx_buf[rx_idx] = b
                rx_idx += 1
                if rx_idx == PACKET_LEN:
                    decoded = ProtocolHarness.decode(bytes(rx_buf))
                    if decoded is not None:
                        decoded_packets.append(decoded)
                        emitted_responses.append("ACK")
                    rx_idx = 0

        return decoded_packets, emitted_responses
