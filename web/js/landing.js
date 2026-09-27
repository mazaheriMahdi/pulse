/**
 * PULSE — Landing Page & Release Showcase Interactive Engine
 * Nothing (R) OS × Teenage Engineering dot-matrix visual simulator
 */

// Available Faces Configuration
const FACES = [
  { id: 'dual', name: 'Dual Load', tag: 'CPU + GPU Split', desc: '5×7 giant numerals, dual horizontal dot gauges, thermal pill readouts.' },
  { id: 'cpu', name: 'CPU Grid', tag: 'Core Diagnostics', desc: '10×10 LED matrix load visualizer, frequency and core metrics.' },
  { id: 'gpu', name: 'GPU Grid', tag: 'NVIDIA Telemetry', desc: 'Dedicated GPU compute, memory saturation, and temperature blip.' },
  { id: 'mem', name: 'Memory', tag: 'RAM / Swap Matrix', desc: 'Active & cached RAM breakdown with dot segmented level gauges.' },
  { id: 'thermal', name: 'Thermal', tag: 'Multi-Zone Heat', desc: 'CPU & GPU core temperature sensors with dynamic warning tags.' },
  { id: 'minimal', name: 'Minimal', tag: 'Focused Single Metric', desc: 'Ultra-high-contrast minimalist single metric with status pill.' },
  { id: 'net', name: 'Network', tag: 'Throughput Meters', desc: 'Dual-channel MB/s meters, peak indicators, and interface badge.' },
  { id: 'clock', name: 'Clock', tag: '24h Time + Seconds Bar', desc: 'Giant 5×7 time digits, blinking Nothing red colon, 60-dot seconds bar, TE ruler.' }
];

let activeFace = 'dual';
let simulatedMetrics = {
  cpu_usage: 28,
  gpu_usage: 44,
  cpu_temp: 46,
  gpu_temp: 52,
  ram_used: 8.4,
  ram_total: 32.0,
  swap_used: 0.8,
  swap_total: 8.0,
  net_rx_rate: 3.42,
  net_tx_rate: 0.85
};

// Auto-scale hero screen to fit responsive chassis
function resizeScreen() {
  const viewport = document.getElementById('hero-viewport');
  const screen = document.getElementById('hero-screen');
  if (!viewport || !screen) return;

  const vpWidth = viewport.clientWidth;
  const scale = vpWidth / 480;
  screen.style.transform = `scale(${scale})`;
}

// Switch Active Face
function setFace(faceId) {
  activeFace = faceId;
  
  // Update buttons
  document.querySelectorAll('.face-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.face === faceId);
  });

  // Update gallery cards
  document.querySelectorAll('.gallery-card').forEach(card => {
    card.classList.toggle('active', card.dataset.face === faceId);
  });

  renderActiveFace();
}

// 5x7 Glyph generator for dot-matrix font
const GLYPHS = {
  '0': [0x1F, 0x11, 0x11, 0x11, 0x1F],
  '1': [0x00, 0x01, 0x1F, 0x01, 0x00],
  '2': [0x17, 0x15, 0x15, 0x15, 0x1D],
  '3': [0x15, 0x15, 0x15, 0x15, 0x1F],
  '4': [0x07, 0x04, 0x04, 0x1F, 0x04],
  '5': [0x1D, 0x15, 0x15, 0x15, 0x17],
  '6': [0x1F, 0x15, 0x15, 0x15, 0x17],
  '7': [0x01, 0x01, 0x19, 0x05, 0x03],
  '8': [0x1F, 0x15, 0x15, 0x15, 0x1F],
  '9': [0x1D, 0x15, 0x15, 0x15, 0x1F],
  ':': [0x00, 0x0A, 0x0A, 0x00, 0x00],
  ' ': [0x00, 0x00, 0x00, 0x00, 0x00]
};

function renderDotDigit(digit, size = 6, gap = 2, color = '#ffffff') {
  const glyph = GLYPHS[digit] || GLYPHS[' '];
  let svg = `<svg class="ndot-digit" width="${5 * size + 4 * gap}" height="${7 * size + 6 * gap}" viewBox="0 0 ${5 * size + 4 * gap} ${7 * size + 6 * gap}">`;
  
  for (let col = 0; col < 5; col++) {
    const colByte = glyph[col];
    for (let row = 0; row < 7; row++) {
      if ((colByte >> (6 - row)) & 1) {
        const x = col * (size + gap);
        const y = row * (size + gap);
        svg += `<circle cx="${x + size/2}" cy="${y + size/2}" r="${size/2}" fill="${color}" />`;
      }
    }
  }
  svg += `</svg>`;
  return svg;
}

// Render Face in Hero Screen
function renderActiveFace() {
  const screen = document.getElementById('hero-screen');
  if (!screen) return;

  const now = new Date();
  const hrs = String(now.getHours()).padStart(2, '0');
  const mins = String(now.getMinutes()).padStart(2, '0');
  const secs = String(now.getSeconds()).padStart(2, '0');
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

  let html = '';

  switch (activeFace) {
    case 'clock':
      let secDots = '';
      for (let i = 0; i < 60; i++) {
        const filled = i <= now.getSeconds();
        const isFive = i % 5 === 0;
        secDots += `<div class="s-dot ${filled ? 'on' : ''} ${isFive ? 'five' : ''}"></div>`;
      }
      html = `
        <div class="face face-clock">
          <div class="clock-head">
            <span class="clock-title">PULSE // LOCAL TIME</span>
            <span class="clock-tz">UTC+03:30</span>
          </div>
          <div class="clock-display">
            <div class="time-block">${renderDotDigit(hrs[0], 7, 3)}${renderDotDigit(hrs[1], 7, 3)}</div>
            <div class="colon-sep">${renderDotDigit(':', 7, 3, '#d71920')}</div>
            <div class="time-block">${renderDotDigit(mins[0], 7, 3)}${renderDotDigit(mins[1], 7, 3)}</div>
            <div class="ampm-pill">${now.getHours() >= 12 ? 'PM' : 'AM'}</div>
          </div>
          <div class="seconds-bar">${secDots}</div>
          <div class="clock-foot">
            <span>${days[now.getDay()]} · ${now.getDate()} ${months[now.getMonth()]}</span>
            <span class="sec-readout">SEC: ${secs}</span>
          </div>
          <div class="te-ruler"></div>
        </div>
      `;
      break;

    case 'dual':
      html = `
        <div class="face face-dual">
          <div class="face-header">
            <div class="brand-tag">PULSE // DUAL TELEMETRY</div>
            <div class="status-tag live">LIVE</div>
          </div>
          <div class="dual-row">
            <div class="dual-col">
              <div class="label-row"><span>CPU LOAD</span><span class="val-pct">${Math.round(simulatedMetrics.cpu_usage)}%</span></div>
              <div class="giant-num">${renderDotDigit(String(Math.floor(simulatedMetrics.cpu_usage/10)), 6, 2)}${renderDotDigit(String(Math.floor(simulatedMetrics.cpu_usage%10)), 6, 2)}</div>
              <div class="meter-track"><div class="meter-fill" style="width: ${simulatedMetrics.cpu_usage}%"></div></div>
              <div class="metric-pill">TEMP: ${Math.round(simulatedMetrics.cpu_temp)}°C</div>
            </div>
            <div class="dual-col">
              <div class="label-row"><span>GPU LOAD</span><span class="val-pct">${Math.round(simulatedMetrics.gpu_usage)}%</span></div>
              <div class="giant-num">${renderDotDigit(String(Math.floor(simulatedMetrics.gpu_usage/10)), 6, 2)}${renderDotDigit(String(Math.floor(simulatedMetrics.gpu_usage%10)), 6, 2)}</div>
              <div class="meter-track"><div class="meter-fill red" style="width: ${simulatedMetrics.gpu_usage}%"></div></div>
              <div class="metric-pill">TEMP: ${Math.round(simulatedMetrics.gpu_temp)}°C</div>
            </div>
          </div>
          <div class="te-ruler"></div>
        </div>
      `;
      break;

    case 'cpu':
      let matrixDots = '';
      const totalActive = Math.round(simulatedMetrics.cpu_usage);
      for (let i = 0; i < 100; i++) {
        matrixDots += `<div class="grid-dot ${i < totalActive ? 'active' : ''}"></div>`;
      }
      html = `
        <div class="face face-cpu">
          <div class="face-header">
            <div class="brand-tag">PULSE // CPU MATRIX</div>
            <div class="val-pct">${Math.round(simulatedMetrics.cpu_usage)}%</div>
          </div>
          <div class="cpu-grid-container">${matrixDots}</div>
          <div class="cpu-footer-stats">
            <div>CORES: 16 ACTIVE</div>
            <div>FREQ: 4.85 GHz</div>
            <div>TEMP: ${Math.round(simulatedMetrics.cpu_temp)}°C</div>
          </div>
          <div class="te-ruler"></div>
        </div>
      `;
      break;

    case 'net':
      html = `
        <div class="face face-net">
          <div class="face-header">
            <div class="brand-tag">PULSE // NETWORK I/O</div>
            <div class="status-tag">WLAN0 · 1.2 Gbps</div>
          </div>
          <div class="net-channels">
            <div class="net-chan">
              <div class="net-label"><span>↓ DOWNSTREAM</span><span class="net-speed">${simulatedMetrics.net_rx_rate.toFixed(2)} MB/s</span></div>
              <div class="meter-track"><div class="meter-fill" style="width: ${Math.min(100, simulatedMetrics.net_rx_rate * 12)}%"></div></div>
            </div>
            <div class="net-chan">
              <div class="net-label"><span>↑ UPSTREAM</span><span class="net-speed red">${simulatedMetrics.net_tx_rate.toFixed(2)} MB/s</span></div>
              <div class="meter-track"><div class="meter-fill red" style="width: ${Math.min(100, simulatedMetrics.net_tx_rate * 25)}%"></div></div>
            </div>
          </div>
          <div class="te-ruler"></div>
        </div>
      `;
      break;

    default:
      // General Fallback
      html = `
        <div class="face face-dual">
          <div class="face-header">
            <div class="brand-tag">PULSE // ${activeFace.toUpperCase()}</div>
            <div class="status-tag">ACTIVE</div>
          </div>
          <div style="padding: 40px 20px; text-align: center;">
            <div style="font-size: 28px; font-weight: 800; margin-bottom: 12px; color: #fff;">${activeFace.toUpperCase()} FACE</div>
            <div style="font-size: 12px; color: #777;">REAL-TIME HARDWARE MONITORING ACTIVE</div>
          </div>
          <div class="te-ruler"></div>
        </div>
      `;
      break;
  }

  screen.innerHTML = html;
}

// Tick Simulation Engine
function tick() {
  // Drift telemetry values gently
  simulatedMetrics.cpu_usage += (Math.random() - 0.48) * 4;
  simulatedMetrics.cpu_usage = Math.max(8, Math.min(94, simulatedMetrics.cpu_usage));

  simulatedMetrics.gpu_usage += (Math.random() - 0.49) * 3;
  simulatedMetrics.gpu_usage = Math.max(12, Math.min(98, simulatedMetrics.gpu_usage));

  simulatedMetrics.cpu_temp = 42 + (simulatedMetrics.cpu_usage * 0.35);
  simulatedMetrics.gpu_temp = 48 + (simulatedMetrics.gpu_usage * 0.38);

  simulatedMetrics.net_rx_rate += (Math.random() - 0.45) * 0.4;
  simulatedMetrics.net_rx_rate = Math.max(0.2, Math.min(18.5, simulatedMetrics.net_rx_rate));

  simulatedMetrics.net_tx_rate += (Math.random() - 0.48) * 0.15;
  simulatedMetrics.net_tx_rate = Math.max(0.05, Math.min(6.2, simulatedMetrics.net_tx_rate));

  renderActiveFace();
}

// Copy to Clipboard
function copyCommand(text, btnId) {
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById(btnId);
    if (btn) {
      const orig = btn.innerText;
      btn.innerText = 'COPIED!';
      setTimeout(() => { btn.innerText = orig; }, 1800);
    }
  });
}

// Face gallery thumbnails
function initGallery() {
  const grid = document.getElementById('face-gallery-grid');
  if (!grid) return;

  grid.innerHTML = FACES.map(f => `
    <div class="gallery-card ${f.id === activeFace ? 'active' : ''}" data-face="${f.id}" onclick="setFace('${f.id}')">
      <div class="gallery-thumb">
        <div style="font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: #fff;">[ ${f.name.toUpperCase()} ]</div>
      </div>
      <div class="gallery-info">
        <div>
          <div class="gallery-name">${f.name}</div>
          <div class="gallery-tag">${f.tag}</div>
        </div>
        <span class="tag red">VIEW</span>
      </div>
    </div>
  `).join('');
}

// Initialize on Load
window.addEventListener('DOMContentLoaded', () => {
  initGallery();
  resizeScreen();
  renderActiveFace();
  setInterval(tick, 600);
  window.addEventListener('resize', resizeScreen);
});
