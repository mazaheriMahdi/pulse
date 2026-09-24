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

**PULSE Studio**:
The native desktop companion application providing a live visual preview of gadget faces, configuration controls, preset management, and serial communication to configure the gadget.
_Avoid_: Web app, web page, dashboard site, configurator

**Face**:
A distinct, self-contained visual screen layout running on the gadget (e.g. CPU Grid, GPU Grid, Dual Load, Memory, Thermal, Minimal).
_Avoid_: Theme, skin, page, screen mode

**Configuration Packet**:
A compact binary command frame sent from PULSE Studio over the serial connection to dynamically switch active faces, colors, and layout options without reflashing microcontroller flash memory.
_Avoid_: Config JSON, setup payload, flash command

**Face Preset**:
A user-saved bundle of visual options (chosen face, accent color, refresh rate, brightness, and label visibility) stored on the host filesystem in JSON format.
_Avoid_: Profile, template, skin file

