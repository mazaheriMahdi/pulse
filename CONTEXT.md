# Performance Monitor Gadget

A physical desktop companion device displaying laptop performance telemetry with real-time CPU, GPU, RAM, temperature, and battery gauges.

## Language

**Telemetry Packet**:
A compact binary-encoded payload transmitted periodically over serial from the host to the gadget.
_Avoid_: Event, message, payload, frame

**Host Agent**:
The laptop background daemon that samples hardware metrics (kernel `/proc/stat`, hwmon, `nvidia-smi`) and transmits Telemetry Packets.
_Avoid_: Server, client, runner, collector

**Gadget Firmware**:
The embedded application executing on the microcontroller driving the TFT display.
_Avoid_: Client, device code, embedded script

**Metric Gauge**:
A visual display element rendering a real-time numerical reading alongside a graphical level bar.
_Avoid_: Progress bar, chart, indicator
