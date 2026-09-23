#![no_std]

pub mod display;
pub mod font;
pub mod ndot;
pub mod numeral;
pub mod traits;
pub mod ui;

pub use display::{Color, Ili9488, HEIGHT, WIDTH};
pub use traits::{DelayMs, Display, PinWrite, SpiWrite};
pub use ui::Dashboard;

