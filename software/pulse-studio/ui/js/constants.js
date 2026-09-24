/* ============================================================
   PULSE STUDIO — Application Constants
   ============================================================ */

export const AVAILABLE_FACES = [
  { id: 'dual',    faceId: 2, name: 'DUAL LOAD',   short: 'CPU+GPU' },
  { id: 'cpu',     faceId: 0, name: 'CPU GRID',    short: 'CPU'    },
  { id: 'gpu',     faceId: 1, name: 'GPU GRID',    short: 'GPU'    },
  { id: 'ram',     faceId: 3, name: 'MEMORY',      short: 'RAM'    },
  { id: 'thermal', faceId: 4, name: 'THERMAL',     short: 'TEMP'   },
  { id: 'minimal', faceId: 5, name: 'MINIMAL',     short: 'ONE'    },
];

export const ACCENT_PALETTE = [
  { hex: '#ffffff', id: 0, name: 'White' },
  { hex: '#d71921', id: 1, name: 'Red' },
  { hex: '#ff5a00', id: 2, name: 'Orange' },
  { hex: '#2ee6c5', id: 3, name: 'Cyan' },
  { hex: '#8b8cf9', id: 4, name: 'Purple' },
  { hex: '#ffc247', id: 5, name: 'Gold' },
];

export const DEFAULT_SETTINGS = {
  face: 'dual',
  accent: '#ffffff',
  refresh: 5,
  brightness: 80,
  label: true,
  temp: true,
  units: true,
  invert: false,
  auto: true,
};

export const INITIAL_TELEMETRY = {
  cpu: 28,
  cpuT: 54,
  gpu: 42,
  gpuT: 49,
  ram: 56,
  ramT: 42,
  battery: 100,
};
