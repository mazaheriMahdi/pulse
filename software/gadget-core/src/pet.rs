//! Cute Companion Pet Sprite & Animation Engine.
//! Renders 24x24 expressive pixel-art desk pets scaled cleanly to 96x96.

use crate::display::{Color, Ili9488};
use crate::traits::{PinWrite, SpiWrite};
use gadget_common::PetMood;

pub const PET_PIXELS: usize = 24;

// Palette indices:
// 0: Background
// 1: Body (Fur)
// 2: Outline/Eyes/Mouth
// 3: Blush/Cheeks/Tongue
// 4: Special (Sweat / Fire / Zzz)
#[derive(Copy, Clone)]
pub struct PetFrame {
    pub rows: [u32; 24],
    pub detail_rows: [u32; 24],
    pub accent_rows: [u32; 24],
}

// Cat / Robot companion sprites
// Base Cat Body silhouette:
// Ears at rows 2-6, round head at rows 7-20, paws at 21-22
static CAT_BODY: [u32; 24] = [
    0x000000, // 0
    0x000000, // 1
    0x060060, // 2  ears top
    0x0F00F0, // 3  ears
    0x1F00F8, // 4  ears
    0x3F81FC, // 5  ears to head
    0x7FFFFE, // 6  top of head
    0xFFFFFF, // 7
    0xFFFFFF, // 8
    0xFFFFFF, // 9
    0xFFFFFF, // 10
    0xFFFFFF, // 11
    0xFFFFFF, // 12
    0xFFFFFF, // 13
    0xFFFFFF, // 14
    0xFFFFFF, // 15
    0xFFFFFF, // 16
    0x7FFFFE, // 17
    0x7FFFFE, // 18
    0x3FFFFC, // 19
    0x3FFFFC, // 20
    0x3E7E7C, // 21 paws
    0x1C3C38, // 22 paws
    0x000000, // 23
];

pub struct CompanionPet {
    pub current_mood: PetMood,
    pub anim_tick: u8,
}

impl CompanionPet {
    pub fn new() -> Self {
        Self {
            current_mood: PetMood::Happy,
            anim_tick: 0,
        }
    }

    pub fn set_mood(&mut self, mood: PetMood) {
        self.current_mood = mood;
    }

    pub fn tick(&mut self) {
        self.anim_tick = self.anim_tick.wrapping_add(1);
    }

    pub fn mood_title(&self) -> &'static str {
        match self.current_mood {
            PetMood::Happy => "CHILLING ^_^",
            PetMood::Focused => "WORKING >_<",
            PetMood::Sweating => "SWEATING ;_;",
            PetMood::Panicked => "PANICKING!!",
            PetMood::Fire => "BURNING OVERHEAT!",
            PetMood::Sleeping => "SLEEPING ZZZ",
            PetMood::Auto => "MONITORING...",
        }
    }

    pub fn mood_badge_color(&self) -> Color {
        match self.current_mood {
            PetMood::Happy => Color::GREEN,
            PetMood::Focused => Color::CYAN,
            PetMood::Sweating => Color::YELLOW,
            PetMood::Panicked => Color::ORANGE,
            PetMood::Fire => Color::RED,
            PetMood::Sleeping => Color::PURPLE,
            PetMood::Auto => Color::TEXT_MUTED,
        }
    }

    pub fn render<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
        &self,
        display: &mut Ili9488<SPI, CS, DC, RST>,
        origin_x: u16,
        origin_y: u16,
        scale: u8,
        bg: Color,
    ) {
        let frame_phase = (self.anim_tick / 2) % 2 == 0;
        let scale = scale.max(1);

        let fur_color = Color::new(245, 235, 220); // Cream white fur
        let ear_pink = Color::PINK;
        let dark_ink = Color::new(30, 30, 45);     // Eyes & outline

        // Render each 24x24 cell
        for r in 0..24 {
            let body_mask = CAT_BODY[r];
            let py = origin_y + (r as u16) * (scale as u16);

            for c in 0..24 {
                let px = origin_x + (c as u16) * (scale as u16);
                let bit = 1 << (23 - c);
                let in_body = (body_mask & bit) != 0;

                let mut pixel_color = if in_body { fur_color } else { bg };

                // Inner ears
                if (r >= 3 && r <= 5) && ((c >= 4 && c <= 6) || (c >= 17 && c <= 19)) {
                    pixel_color = ear_pink;
                }

                // Eyes, mouth, and mood features
                match self.current_mood {
                    PetMood::Happy | PetMood::Auto => {
                        // Smiling arch eyes: (^  ^)
                        let eye_row = if frame_phase { 11 } else { 12 };
                        if r == eye_row && ((c >= 5 && c <= 7) || (c >= 16 && c <= 18)) {
                            pixel_color = dark_ink;
                        }
                        if r == eye_row - 1 && ((c == 6) || (c == 17)) {
                            pixel_color = dark_ink;
                        }
                        // Cute cat mouth :3
                        if (r == 14 && (c == 11 || c == 12)) || (r == 15 && (c == 10 || c == 13)) {
                            pixel_color = dark_ink;
                        }
                        // Cheeks
                        if r == 14 && ((c == 4 || c == 5) || (c == 18 || c == 19)) {
                            pixel_color = ear_pink;
                        }
                    }
                    PetMood::Focused => {
                        // Big round alert eyes: (•  •)
                        if (r >= 10 && r <= 12) && ((c >= 5 && c <= 7) || (c >= 16 && c <= 18)) {
                            // Highlight in eye
                            if r == 10 && (c == 5 || c == 16) {
                                pixel_color = Color::WHITE;
                            } else {
                                pixel_color = dark_ink;
                            }
                        }
                        // Small serious mouth
                        if r == 15 && (c >= 11 && c <= 12) {
                            pixel_color = dark_ink;
                        }
                    }
                    PetMood::Sweating => {
                        // Worried eyes:
                        if (r == 11) && ((c >= 5 && c <= 7) || (c >= 16 && c <= 18)) {
                            pixel_color = dark_ink;
                        }
                        // Big sweat drop on side of head (CYAN)
                        let sweat_y = if frame_phase { 6 } else { 7 };
                        if (r >= sweat_y && r <= sweat_y + 2) && (c == 20 || c == 21) {
                            pixel_color = Color::CYAN;
                        }
                        // Wavy mouth
                        if (r == 14 && c == 10) || (r == 15 && (c == 11 || c == 12)) || (r == 14 && c == 13) {
                            pixel_color = dark_ink;
                        }
                    }
                    PetMood::Panicked => {
                        // Wide open screaming mouth and > < eyes
                        // Left eye >
                        if (r == 10 && c == 5) || (r == 11 && c == 7) || (r == 12 && c == 5) {
                            pixel_color = dark_ink;
                        }
                        // Right eye <
                        if (r == 10 && c == 18) || (r == 11 && c == 16) || (r == 12 && c == 18) {
                            pixel_color = dark_ink;
                        }
                        // Screaming open mouth (RED inside)
                        if (r >= 14 && r <= 16) && (c >= 10 && c <= 13) {
                            pixel_color = Color::RED;
                        }
                        // Sweat drops both sides
                        if (r == 8 || r == 9) && (c == 2 || c == 21) {
                            pixel_color = Color::CYAN;
                        }
                    }
                    PetMood::Fire => {
                        // Flames rising above head!
                        if r <= 2 {
                            let flame_shift = if frame_phase { 1 } else { 0 };
                            if (c >= 8 + flame_shift && c <= 10 + flame_shift) || (c >= 13 && c <= 15) {
                                pixel_color = if r == 0 { Color::YELLOW } else { Color::RED };
                            }
                        }
                        // Angry blazing eyes
                        if (r >= 10 && r <= 11) && ((c >= 5 && c <= 7) || (c >= 16 && c <= 18)) {
                            pixel_color = Color::RED;
                        }
                        // Open teeth/mouth
                        if (r >= 14 && r <= 15) && (c >= 9 && c <= 14) {
                            pixel_color = Color::BLACK;
                        }
                    }
                    PetMood::Sleeping => {
                        // Closed sleeping eyes: (-  -)
                        if r == 12 && ((c >= 5 && c <= 7) || (c >= 16 && c <= 18)) {
                            pixel_color = dark_ink;
                        }
                        // Sleeping mouth .
                        if r == 14 && c == 11 {
                            pixel_color = dark_ink;
                        }
                        // Floating 'Z' above head
                        let z_y = if frame_phase { 2 } else { 3 };
                        if (r == z_y && (c >= 18 && c <= 20))
                            || (r == z_y + 1 && c == 19)
                            || (r == z_y + 2 && (c >= 18 && c <= 20))
                        {
                            pixel_color = Color::CYAN;
                        }
                    }
                }

                display.fill_rect(px, py, scale as u16, scale as u16, pixel_color);
            }
        }
    }
}
