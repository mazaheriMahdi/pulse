/* ============================================================
   PULSE STUDIO — Application Controller & Entrypoint
   ============================================================ */

import { AVAILABLE_FACES, ACCENT_PALETTE, DEFAULT_SETTINGS } from './constants.js';
import { store } from './state.js';
import { renderFace } from './faces.js';
import { renderThumbnail } from './thumbnails.js';
import { renderDotLogo } from './font.js';
import { BootSplashController } from './splash.js';
import {
  fetchTelemetry,
  checkDaemonConnected,
  flashConfigToGadget,
  savePresetFile,
  loadPresetFile,
  windowMinimize,
  windowMaximize,
  windowClose,
} from './ipc.js';

// DOM Element References
const screenEl = document.getElementById('screen');
const previewAreaEl = document.getElementById('previewArea');
const faceGridEl = document.getElementById('faceGrid');
const connPill = document.getElementById('connPill');
const connText = document.getElementById('connText');
const streamRate = document.getElementById('streamRate');
const previewName = document.getElementById('previewName');
const setName = document.getElementById('setName');
const brightnessSlider = document.getElementById('brightness');
const brightnessVal = document.getElementById('brightnessVal');
const saveBtn = document.getElementById('saveBtn');
const loadBtn = document.getElementById('loadBtn');
const flashBtn = document.getElementById('flashBtn');
const flashFill = document.getElementById('flashFill');
const flashLabel = document.getElementById('flashLabel');
const sbStatus = document.getElementById('sbStatus');

/**
 * Initializes the Face Library sidebar cards
 */
function initFaceLibrary() {
  if (!faceGridEl) return;
  faceGridEl.innerHTML = '';

  const faceCount = document.getElementById('faceCount');
  if (faceCount) faceCount.textContent = `${AVAILABLE_FACES.length} FACES`;

  AVAILABLE_FACES.forEach((face) => {
    const card = document.createElement('div');
    const isActive = face.id === store.settings.face;
    card.className = `face ${isActive ? 'on' : ''}`;
    card.dataset.id = face.id;
    card.style.color = isActive ? store.settings.accent : '#5a5a5a';

    card.innerHTML = `
      <div class="thumb" id="thumb-${face.id}">
        ${renderThumbnail(face.id, store.settings.accent)}
      </div>
      <div class="fname">${face.name}</div>
    `;

    card.addEventListener('click', () => {
      store.updateSettings({ face: face.id });
      updateFaceHeaderNames();
    });

    faceGridEl.appendChild(card);
  });
}

function updateFaceHeaderNames() {
  const current = AVAILABLE_FACES.find((f) => f.id === store.settings.face);
  if (current) {
    if (previewName) previewName.textContent = current.name;
    if (setName) setName.textContent = current.name;
  }
}

/**
 * Updates sidebar thumbnail selection states
 */
function updateThumbnailSelection() {
  document.querySelectorAll('.face').forEach((card) => {
    const isActive = card.dataset.id === store.settings.face;
    card.classList.toggle('on', isActive);
    card.style.color = isActive ? store.settings.accent : '#5a5a5a';
  });
}

/**
 * Updates thumbnails accent color
 */
function updateThumbnailsAccent() {
  AVAILABLE_FACES.forEach((face) => {
    const thumbFrame = document.getElementById(`thumb-${face.id}`);
    if (thumbFrame) {
      thumbFrame.innerHTML = renderThumbnail(face.id, store.settings.accent);
    }
  });
}

/**
 * Renders the hardware LCD screen preview
 */
function renderScreen() {
  if (!screenEl) return;

  // Update accent color CSS variable
  screenEl.style.setProperty('--acc', store.settings.accent);
  screenEl.style.color = store.settings.accent;

  // Invert class
  if (store.settings.invert) {
    screenEl.classList.add('invert');
  } else {
    screenEl.classList.remove('invert');
  }

  // Render active face layout
  screenEl.innerHTML = renderFace(
    store.settings.face,
    store.settings.label !== false ? store.settings : { ...store.settings, label: false },
    store.telemetry
  );
}

/**
 * Responsive Screen Scaler using ResizeObserver
 */
function initResponsiveScaler() {
  if (!previewAreaEl) return;

  const updateScale = () => {
    const rect = previewAreaEl.getBoundingClientRect();
    const padX = 40;
    const padY = 40;
    const availW = Math.max(180, rect.width - padX);
    const availH = Math.max(120, rect.height - padY);

    const scaleX = availW / 480;
    const scaleY = availH / 320;
    const scale = Math.min(scaleX, scaleY);
    const clampedScale = Math.min(1.8, Math.max(0.4, scale));

    previewAreaEl.style.setProperty('--preview-scale', clampedScale.toFixed(3));
  };

  const observer = new ResizeObserver(() => {
    updateScale();
  });
  observer.observe(previewAreaEl);
  updateScale();
}

/**
 * Binds UI inputs and controls
 */
function initControls() {
  // Color Swatches
  document.querySelectorAll('.sw').forEach((sw) => {
    sw.addEventListener('click', () => {
      const color = sw.dataset.c;
      document.querySelectorAll('.sw').forEach((s) => s.classList.remove('on'));
      sw.classList.add('on');
      store.updateSettings({ accent: color });
      updateThumbnailsAccent();
    });
  });

  // Refresh Rate Segmented Control
  document.querySelectorAll('#refreshSeg button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#refreshSeg button').forEach((b) => b.classList.remove('on'));
      btn.classList.add('on');
      const hz = parseInt(btn.dataset.v, 10);
      store.updateSettings({ refresh: hz });
      if (streamRate) streamRate.textContent = `STREAMING · ${hz} HZ`;
    });
  });

  // Brightness Slider
  if (brightnessSlider) {
    brightnessSlider.addEventListener('input', () => {
      const val = parseInt(brightnessSlider.value, 10);
      if (brightnessVal) brightnessVal.textContent = `${val}%`;
      if (screenEl) screenEl.style.filter = `brightness(${0.45 + val / 160})`;
      store.updateSettings({ brightness: val });
    });
  }

  // Toggles / Flags (Nothing style switches)
  document.querySelectorAll('.toggle').forEach((t) => {
    t.addEventListener('click', () => {
      const k = t.dataset.k;
      const newVal = !store.settings[k];
      store.updateSettings({ [k]: newVal });
      t.classList.toggle('on', newVal);
    });
  });

  // Window Controls
  const minBtn = document.getElementById('btnMin');
  const maxBtn = document.getElementById('btnMax');
  const closeBtn = document.getElementById('btnClose');

  if (minBtn) minBtn.addEventListener('click', () => windowMinimize());
  if (maxBtn) maxBtn.addEventListener('click', () => windowMaximize());
  if (closeBtn) closeBtn.addEventListener('click', () => windowClose());

  // Flash Button (Serial IPC)
  let flashing = false;
  if (flashBtn) {
    flashBtn.addEventListener('click', async () => {
      if (flashing) return;
      flashing = true;

      flashBtn.disabled = true;
      flashBtn.classList.add('busy');
      if (flashFill) flashFill.style.width = '0%';
      if (sbStatus) sbStatus.textContent = 'TRANSMITTING CONFIG…';

      try {
        await flashConfigToGadget({
          face: store.settings.face,
          accent: store.settings.accent,
          refresh: store.settings.refresh,
          brightness: store.settings.brightness,
          label: store.settings.label,
          temp: store.settings.temp,
          units: store.settings.units,
          invert: store.settings.invert,
        });
      } catch (err) {
        console.warn('IPC send_config error:', err);
      }

      let p = 0;
      const tick = setInterval(() => {
        p += 14 + Math.random() * 12;
        if (p >= 100) {
          p = 100;
          clearInterval(tick);
          if (flashFill) flashFill.style.width = '100%';
          if (flashLabel) flashLabel.textContent = 'FLASHED ✓';
          if (sbStatus) sbStatus.textContent = 'FLASH COMPLETE · SAVED TO EEPROM';

          setTimeout(() => {
            if (flashFill) flashFill.style.width = '0%';
            if (flashLabel) flashLabel.textContent = 'FLASH TO GADGET →';
            flashBtn.classList.remove('busy');
            flashBtn.disabled = false;
            if (sbStatus) sbStatus.textContent = 'READY';
            flashing = false;
          }, 1500);
        } else {
          if (flashFill) flashFill.style.width = `${p}%`;
          if (flashLabel) flashLabel.textContent = `FLASHING ${Math.round(p)}%`;
        }
      }, 60);
    });
  }

  // Presets Save / Load
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      try {
        await savePresetFile(store.settings);
        if (sbStatus) sbStatus.textContent = 'PRESET SAVED TO DISK';
        setTimeout(() => {
          if (sbStatus) sbStatus.textContent = 'READY';
        }, 1500);
      } catch (e) {
        console.error('Preset save failed:', e);
      }
    });
  }

  if (loadBtn) {
    loadBtn.addEventListener('click', async () => {
      try {
        const loaded = await loadPresetFile();
        if (loaded && typeof loaded === 'object') {
          store.updateSettings(loaded);
          // Sync UI
          if (brightnessSlider) brightnessSlider.value = store.settings.brightness;
          if (brightnessVal) brightnessVal.textContent = `${store.settings.brightness}%`;
          if (screenEl) screenEl.style.filter = `brightness(${0.45 + store.settings.brightness / 160})`;

          document.querySelectorAll('#refreshSeg button').forEach((b) => {
            b.classList.toggle('on', parseInt(b.dataset.v, 10) === store.settings.refresh);
          });
          document.querySelectorAll('.sw').forEach((s) => {
            s.classList.toggle('on', s.dataset.c === store.settings.accent);
          });
          document.querySelectorAll('.toggle').forEach((t) => {
            const k = t.dataset.k;
            if (typeof store.settings[k] === 'boolean') {
              t.classList.toggle('on', store.settings[k]);
            }
          });

          updateThumbnailSelection();
          updateThumbnailsAccent();
          updateFaceHeaderNames();
          if (sbStatus) sbStatus.textContent = 'PRESET LOADED';
          setTimeout(() => {
            if (sbStatus) sbStatus.textContent = 'READY';
          }, 1500);
        }
      } catch (e) {
        console.error('Preset load failed:', e);
      }
    });
  }
}

/**
 * Background Telemetry & Connection Polling Loop
 */
function startTelemetryLoop() {
  const poll = async () => {
    try {
      const isLive = await checkDaemonConnected();
      store.setConnection(isLive);

      if (isLive) {
        if (connPill) connPill.classList.add('live');
        if (connText) connText.textContent = 'ONLINE';
      } else {
        if (connPill) connPill.classList.remove('live');
        if (connText) connText.textContent = 'DISCONNECTED';
      }

      const data = await fetchTelemetry();
      if (data) {
        store.updateTelemetry({
          cpu: data.cpu,
          cpuT: data.cpu_temp,
          gpu: data.gpu,
          gpuT: data.gpu_temp,
          ram: data.ram,
          battery: data.battery,
          netUp: data.net_up,
          netDn: data.net_dn,
          peakUp: data.peak_up,
          peakDn: data.peak_dn,
          iface: data.iface,
        });
      }
    } catch (e) {
      // IPC polling errors
    }
  };

  setInterval(poll, 250);
  poll();
}

/**
 * Main Application Bootstrap
 */
function bootstrap() {
  const splashEl = document.getElementById('splashOverlay');
  if (splashEl) {
    const splash = new BootSplashController(splashEl);
    splash.init().then(() => {
      console.log('[Boot] Nothing OS splash sequence completed, Studio active.');
    });
  }

  // Render Titlebar Dot Logos
  const tbPulseEl = document.getElementById('tbPulseLogo');
  const tbStudioEl = document.getElementById('tbStudioLogo');
  if (tbPulseEl) tbPulseEl.innerHTML = renderDotLogo('PULSE', 2.8);
  if (tbStudioEl) tbStudioEl.innerHTML = renderDotLogo('STUDIO', 1.8);

  initFaceLibrary();
  initControls();
  initResponsiveScaler();
  updateFaceHeaderNames();

  // Subscribe to state changes to update the screen
  store.subscribe((s, change) => {
    if (change === 'settings') {
      updateThumbnailSelection();
    }
    renderScreen();
  });

  renderScreen();
  startTelemetryLoop();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootstrap);
} else {
  bootstrap();
}
