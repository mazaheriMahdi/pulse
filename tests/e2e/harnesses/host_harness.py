"""
Host Daemon Execution & Telemetry Harness
Interacts with software/gadget-host CLI, validates process lifecycle,
and evaluates telemetry sampling algorithms from Linux procfs and sysfs.
"""
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TelemetrySample:
    cpu_percent: int
    cpu_temp_c: int
    gpu_percent: int
    gpu_temp_c: int
    ram_percent: int
    battery_percent: int
    timestamp: float


class HostHarness:
    """Harness for testing the Linux host telemetry collector (gadget-host)."""

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            # Anchor to repo root
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..")
            )
        else:
            self.project_root = os.path.abspath(project_root)

        self.host_dir = os.path.join(self.project_root, "software", "gadget-host")
        self.manifest_path = os.path.join(self.host_dir, "Cargo.toml")
        self.bin_path = os.path.join(self.host_dir, "target", "debug", "gadget-host")

    def build_host(self) -> bool:
        """Compiles software/gadget-host in debug mode."""
        cmd = ["cargo", "build", "--manifest-path", self.manifest_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0

    def ensure_built(self) -> str:
        """Ensures host binary is compiled, returning its executable path."""
        if not os.path.exists(self.bin_path):
            success = self.build_host()
            if not success:
                raise RuntimeError("Failed to build software/gadget-host binary via cargo")
        return self.bin_path

    def run_cli_help(self) -> subprocess.CompletedProcess:
        """Executes `gadget-host --help`."""
        bin_p = self.ensure_built()
        return subprocess.run([bin_p, "--help"], capture_output=True, text=True, timeout=5)

    def run_cli_version(self) -> str:
        """Executes `gadget-host --version` and returns version string."""
        bin_p = self.ensure_built()
        res = subprocess.run([bin_p, "--version"], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            raise RuntimeError(f"gadget-host --version failed: {res.stderr}")
        return res.stdout.strip()

    def run_dry_run(self, duration_sec: float = 1.5, interval_ms: int = 200) -> List[TelemetrySample]:
        """
        Executes `gadget-host --dry-run --interval-ms <interval_ms>` for `duration_sec`,
        captures stdout, and parses metric stream records.
        """
        bin_p = self.ensure_built()
        cmd = [bin_p, "--dry-run", "--interval-ms", str(interval_ms)]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        time.sleep(duration_sec)
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        pattern = re.compile(
            r"\[Metrics\]\s+CPU:\s*(\d+)%\s*\((\d+)°C\)\s*\|\s*GPU:\s*(\d+)%\s*\((\d+)°C\)\s*\|\s*RAM:\s*(\d+)%\s*\|\s*Bat:\s*(\d+)%"
        )

        samples: List[TelemetrySample] = []
        for match in pattern.finditer(stdout):
            cpu_p = int(match.group(1))
            cpu_t = int(match.group(2))
            gpu_p = int(match.group(3))
            gpu_t = int(match.group(4))
            ram_p = int(match.group(5))
            bat_p = int(match.group(6))
            samples.append(
                TelemetrySample(
                    cpu_percent=cpu_p,
                    cpu_temp_c=cpu_t,
                    gpu_percent=gpu_p,
                    gpu_temp_c=gpu_t,
                    ram_percent=ram_p,
                    battery_percent=bat_p,
                    timestamp=time.time(),
                )
            )

        return samples

    def run_nonexistent_port(self, port: str = "/dev/nonexistent_serial_e2e") -> Tuple[int, str, str]:
        """
        Executes host with an invalid serial port, verifying graceful fallback to dry-run mode.
        """
        bin_p = self.ensure_built()
        cmd = [bin_p, "--port", port, "--interval-ms", "100"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(0.8)
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        return proc.returncode, stdout, stderr

    # --- Pure Mathematical & Algorithmic Models (matching gadget-host main.rs) ---

    @staticmethod
    def calculate_cpu_percent(prev_idle: int, prev_total: int, curr_idle: int, curr_total: int) -> int:
        """
        Computes CPU busy percentage with saturation subtraction and zero-tick division protection.
        Matches calculate_cpu_percent in software/gadget-host/src/main.rs.
        """
        delta_idle = max(0, curr_idle - prev_idle)
        delta_total = max(0, curr_total - prev_total)

        if delta_total > 0:
            busy = max(0, delta_total - delta_idle)
            pct = round((busy / float(delta_total)) * 100.0)
            return min(100, max(0, int(pct)))
        return 0

    @staticmethod
    def parse_proc_stat(content: str) -> Optional[Tuple[int, int]]:
        """
        Extracts aggregate (idle, total) ticks from /proc/stat.
        Matches parse_proc_stat in software/gadget-host/src/main.rs.
        """
        for line in content.splitlines():
            if line.startswith("cpu "):
                parts = [int(p) for p in line.strip().split()[1:] if p.isdigit()]
                if len(parts) >= 4:
                    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
                    total = sum(parts)
                    return idle, total
        return None

    @staticmethod
    def parse_meminfo_kb(content: str) -> Optional[Tuple[int, int]]:
        """
        Extracts (MemTotal_kB, MemAvailable_kB) from /proc/meminfo.
        """
        total: Optional[int] = None
        available: Optional[int] = None

        for line in content.splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    total = int(parts[1])
            elif line.startswith("MemAvailable:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    available = int(parts[1])
            if total is not None and available is not None:
                break

        if total is not None and available is not None and total > 0:
            return total, available
        return None

    @staticmethod
    def parse_meminfo(content: str) -> Optional[int]:
        """
        Computes RAM percentage from /proc/meminfo content.
        """
        res = HostHarness.parse_meminfo_kb(content)
        if not res:
            return None
        total, avail = res
        used = max(0, total - avail)
        pct = round((used / float(total)) * 100.0)
        return min(100, max(0, int(pct)))

    @staticmethod
    def parse_nvidia_smi(output: str) -> Optional[Tuple[int, int]]:
        """
        Parses comma-delimited output from nvidia-smi: util, temp.
        """
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                util_str = parts[0].rstrip("%").strip()
                temp_str = parts[1].rstrip("C°").strip()
                try:
                    util = min(100, int(util_str))
                    temp = int(temp_str)
                    return util, temp
                except ValueError:
                    continue
        return None

    @staticmethod
    def parse_hwmon_temp(content: str) -> Optional[int]:
        """
        Parses millidegrees Celsius into degrees Celsius.
        """
        try:
            val = int(content.strip())
            temp = val // 1000
            if 0 < temp < 125:
                return temp
        except ValueError:
            pass
        return None

    @staticmethod
    def parse_gpu_busy_percent(content: str) -> Optional[int]:
        """Parses GPU busy percent from sysfs."""
        try:
            val = int(content.strip())
            return min(100, max(0, val))
        except ValueError:
            return None

    @staticmethod
    def select_cpu_temp_sensor(hwmon_drivers: List[Tuple[str, int]]) -> int:
        """
        Demonstrates driver selection priority:
        Priority 1: k10temp / coretemp
        Priority 2: acpitz
        Fallback: 50
        """
        for name, temp in hwmon_drivers:
            if name in ("k10temp", "coretemp"):
                return temp
        for name, temp in hwmon_drivers:
            if name == "acpitz":
                return temp
        return 50
