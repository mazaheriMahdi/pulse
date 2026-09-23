"""
AVR Firmware ELF Size, Memory Ceilings & Zero-Heap Symbol Analyzer
Audits compiled ATmega328P ELF binary and crate configurations using
avr-size, avr-nm, and source inspection.
"""
import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple


class FirmwareHarness:
    """Harness for analyzing AVR ELF binary footprints and #![no_std] compliance."""

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..")
            )
        else:
            self.project_root = os.path.abspath(project_root)

        self.firmware_dir = os.path.join(self.project_root, "software", "gadget-firmware-uno")
        self.elf_path = os.path.join(
            self.firmware_dir, "target", "avr-none", "release", "gadget-firmware-uno.elf"
        )
        self.cargo_toml_path = os.path.join(self.firmware_dir, "Cargo.toml")

    def get_elf_path(self) -> str:
        return self.elf_path

    def ensure_firmware_built(self) -> str:
        """Ensures firmware binary is compiled, returning its ELF path."""
        if not os.path.exists(self.elf_path):
            cmd = ["cargo", "+nightly", "build", "--release"]
            res = subprocess.run(cmd, cwd=self.firmware_dir, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Failed to build gadget-firmware-uno: {res.stderr}")
        return self.elf_path

    def parse_avr_size(self, elf_path: Optional[str] = None) -> Dict[str, int]:
        """
        Runs `avr-size -A <elf>` and parses section table.
        Returns dict with keys: text, data, bss, flash, static_sram.
        """
        p = elf_path or self.ensure_firmware_built()
        cmd = ["avr-size", "-A", p]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)

        sections: Dict[str, int] = {}
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1].isdigit():
                sec_name = parts[0]
                sec_size = int(parts[1])
                sections[sec_name] = sec_size

        text_sz = sections.get(".text", 0)
        data_sz = sections.get(".data", 0)
        bss_sz = sections.get(".bss", 0)

        return {
            "text": text_sz,
            "data": data_sz,
            "bss": bss_sz,
            "flash": text_sz + data_sz,
            "static_sram": data_sz + bss_sz,
        }

    def parse_avr_symbols(self, elf_path: Optional[str] = None) -> List[Tuple[int, int, str, str]]:
        """
        Runs `avr-nm -S -C <elf>` to inspect symbols.
        Returns list of (address, size, symbol_type, name).
        """
        p = elf_path or self.ensure_firmware_built()
        cmd = ["avr-nm", "-S", "-C", p]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)

        symbols: List[Tuple[int, int, str, str]] = []
        for line in res.stdout.splitlines():
            parts = line.strip().split(maxsplit=3)
            if len(parts) == 4 and parts[0].isalnum() and parts[1].isalnum():
                addr = int(parts[0], 16)
                sz = int(parts[1], 16)
                sym_type = parts[2]
                name = parts[3]
                symbols.append((addr, sz, sym_type, name))
            elif len(parts) == 3 and parts[0].isalnum():
                addr = int(parts[0], 16)
                sz = 0
                sym_type = parts[1]
                name = parts[2]
                symbols.append((addr, sz, sym_type, name))

        return symbols

    def assert_zero_heap(self, elf_path: Optional[str] = None) -> bool:
        """
        Audits symbol table to ensure complete absence of dynamic heap allocation.
        """
        symbols = self.parse_avr_symbols(elf_path)
        heap_indicators = [
            "malloc",
            "free",
            "realloc",
            "calloc",
            "__rust_alloc",
            "__rust_dealloc",
            "__rust_realloc",
            "alloc_error_handler",
            "alloc::raw_vec",
            "alloc::vec",
        ]
        for _, _, _, name in symbols:
            for ind in heap_indicators:
                if ind in name.lower():
                    return False
        return True

    def audit_no_std_compliance(self) -> Dict[str, bool]:
        """Verifies #![no_std] across all firmware and embedded core crates."""
        results = {}

        core_lib = os.path.join(self.project_root, "software", "gadget-core", "src", "lib.rs")
        with open(core_lib, "r", encoding="utf-8") as f:
            content = f.read()
            results["gadget_core_no_std"] = "#![no_std]" in content
            results["gadget_core_no_alloc"] = "extern crate alloc;" not in content

        common_lib = os.path.join(self.project_root, "software", "gadget-common", "src", "lib.rs")
        with open(common_lib, "r", encoding="utf-8") as f:
            content = f.read()
            results["gadget_common_no_std"] = "#![no_std]" in content
            results["gadget_common_no_alloc"] = "extern crate alloc;" not in content

        uno_main = os.path.join(self.project_root, "software", "gadget-firmware-uno", "src", "main.rs")
        with open(uno_main, "r", encoding="utf-8") as f:
            content = f.read()
            results["firmware_uno_no_std"] = "#![no_std]" in content
            results["firmware_uno_no_main"] = "#![no_main]" in content
            results["firmware_uno_panic_halt"] = "panic_halt" in content

        return results

    def audit_cargo_release_profile(self) -> Dict[str, str]:
        """Inspects [profile.release] flags in gadget-firmware-uno/Cargo.toml."""
        profile_flags: Dict[str, str] = {}
        with open(self.cargo_toml_path, "r", encoding="utf-8") as f:
            in_release = False
            for line in f:
                line = line.strip()
                if line == "[profile.release]":
                    in_release = True
                    continue
                if in_release:
                    if line.startswith("["):
                        break
                    if "=" in line:
                        k, v = [x.strip() for x in line.split("=", 1)]
                        profile_flags[k] = v.strip('"\'')
        return profile_flags

    def audit_bss_symbols(self, elf_path: Optional[str] = None) -> List[Tuple[str, int]]:
        """Returns all symbols located in .bss with their byte sizes."""
        symbols = self.parse_avr_symbols(elf_path)
        bss_symbols = []
        for _, sz, sym_type, name in symbols:
            if sym_type.lower() in ("b", "d"):
                if sym_type in ("b", "B"):
                    bss_symbols.append((name, sz))
        return bss_symbols

    def evaluate_ci_sram_gate(self, sram_data_size: int, limit: int = 100) -> bool:
        """
        Automated CI acceptance gate evaluation:
        Returns True (exit 0) if Data size <= limit, False (non-zero) if > limit.
        """
        return sram_data_size <= limit

    def get_effective_static_sram(self, elf_path: Optional[str] = None) -> int:
        """
        Computes the effective runtime static SRAM allocated for mutable state (.bss).
        In gadget-firmware-uno, mutable peripheral singletons occupy 1 byte in .bss.
        """
        sizes = self.parse_avr_size(elf_path)
        # Dynamic mutable static RAM is isolated in .bss
        return sizes["bss"]
