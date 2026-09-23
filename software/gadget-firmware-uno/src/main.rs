#![no_std]
#![no_main]

use panic_halt as _;

use arduino_hal::prelude::*;
use arduino_hal::spi;
use gadget_common::{TelemetryPacket, PACKET_LEN};
use gadget_core::{Dashboard, DelayMs, Ili9488, PinWrite, SpiWrite};

struct UnoPin<P>(pub P);

impl<P: embedded_hal_02::digital::v2::OutputPin> PinWrite for UnoPin<P> {
    #[inline(always)]
    fn set_high(&mut self) {
        let _ = self.0.set_high();
    }

    #[inline(always)]
    fn set_low(&mut self) {
        let _ = self.0.set_low();
    }
}

struct UnoSpi<S>(pub S);

impl<S: embedded_hal_02::spi::FullDuplex<u8>> SpiWrite for UnoSpi<S> {
    #[inline(always)]
    fn write_byte(&mut self, byte: u8) {
        let _ = nb::block!(self.0.send(byte));
        let _ = nb::block!(self.0.read());
    }
}

struct UnoDelay;

impl DelayMs for UnoDelay {
    #[inline(always)]
    fn delay_ms(&mut self, ms: u16) {
        arduino_hal::delay_ms(ms as u32);
    }
}

#[arduino_hal::entry]
fn main() -> ! {
    let dp = arduino_hal::Peripherals::take().unwrap();
    let pins = arduino_hal::pins!(dp);

    // Serial console for receiving TelemetryPackets from laptop host
    let mut serial = arduino_hal::default_serial!(dp, pins, 115200);

    // Hardware SPI on Uno: D13 (SCK), D11 (MOSI), D12 (MISO)
    // CS is on D10
    // DC / RS is on D9
    // RESET is on D8
    let (spi_bus, cs_pin) = arduino_hal::Spi::new(
        dp.SPI,
        pins.d13.into_output(),
        pins.d11.into_output(),
        pins.d12.into_pull_up_input(),
        pins.d10.into_output(),
        spi::Settings {
            data_order: spi::DataOrder::MostSignificantFirst,
            clock: spi::SerialClockRate::OscfOver2, // 8 MHz
            mode: embedded_hal::spi::MODE_0,
        },
    );

    let cs = UnoPin(cs_pin);
    let dc = UnoPin(pins.d9.into_output());
    let rst = UnoPin(pins.d8.into_output());
    let spi_writer = UnoSpi(spi_bus);

    let mut display = Ili9488::new(spi_writer, cs, dc, rst);
    let mut delay = UnoDelay;

    // Initialize display with hardware reset sequence & registers
    display.init(&mut delay);

    // Create dashboard UI
    let mut dashboard = Dashboard::new();
    dashboard.draw_layout(&mut display);

    // Render initial zeroed telemetry waiting for host daemon
    let mut current_packet = TelemetryPacket::new(0, 0, 0, 0, 0, 100);
    dashboard.update(&mut display, current_packet);

    let _ = ufmt::uwriteln!(&mut serial, "GADGET_READY");

    let mut rx_buf = [0u8; PACKET_LEN];
    let mut rx_idx: usize = 0;

    loop {
        // Read serial data without blocking
        match serial.read() {
            Ok(b) => {
                if rx_idx == 0 {
                    if b == gadget_common::MAGIC_0 {
                        rx_buf[0] = b;
                        rx_idx = 1;
                    }
                } else if rx_idx == 1 {
                    if b == gadget_common::MAGIC_1 {
                        rx_buf[1] = b;
                        rx_idx = 2;
                    } else if b == gadget_common::MAGIC_0 {
                        rx_idx = 1;
                    } else {
                        rx_idx = 0;
                    }
                } else {
                    rx_buf[rx_idx] = b;
                    rx_idx += 1;

                    if rx_idx == PACKET_LEN {
                        if let Some(packet) = TelemetryPacket::decode(&rx_buf) {
                            current_packet = packet;
                            dashboard.update(&mut display, current_packet);
                            let _ = ufmt::uwriteln!(&mut serial, "ACK");
                        }
                        rx_idx = 0;
                    }
                }
            }
            Err(nb::Error::WouldBlock) => {}
            Err(_) => {
                rx_idx = 0;
            }
        }
    }
}
