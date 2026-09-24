/* ============================================================
   PULSE STUDIO — Application Controller & Entrypoint
   ============================================================ */

import { AVAILABLE_FACES, ACCENT_PALETTE, DEFAULT_SETTINGS } from './constants.js';
import { store } from './state.js';
import { renderFace } from './faces.js';
import { renderThumbnail } from './thumbnails.js';
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
const previewAreaEl = document.getElementById('preview-area');
const facesGridEl = document.getElementById('faces-grid');
const flashBtn = document.getElementById('flash-btn');
const flashStatusEl = document.getElementById('flash-status');
const connPillEl = document.getElementById('conn-pill');
const connStatusText = document.getElementById('conn-status-text');
const brightnessSlider = document.getElementById('brightness-slider');
const brightnessValEl = document.getElementById('brightness-val');

/**
 * Initializes the Face Library sidebar cards
 */
function initFaceLibrary() {
  if (!facesGridEl) return;
  facesGridEl.innerHTML = '';

  AVAILABLE_FACES.forEach((face) => {
    const card = document.createElement('div');
    card.className = `face-card ${face.id === store.settings.face ? 'active' : ''}`;
    card.dataset.faceId = face.id;

    card.innerHTML = `
      <div class="thumb-frame" id="thumb-${face.id}">
        ${renderThumbnail(face.id, store.settings.accent)}
      </div>
      <div class="card-meta">
        <span class="face-name">${face.name}</span>
        <span class="face-tag">${face.short}</span>
      </div>
    `;

    card.addEventListener('click', () => {
      store.updateSettings({ face: face.id });
    });

    facesGridEl.appendChild(card);
  });
}

/**
 * Updates sidebar thumbnail selection states
 */
function updateThumbnailSelection() {
  document.querySelectorAll('.face-card').forEach((card) => {
    if (card.dataset.faceId === store.settings.face) {
      card.classList.add('active');
    } else {
      card.classList.remove('active');
    }
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

  // Invert class
  if (store.settings.invert) {
    screenEl.classList.add('invert');
  } else {
    screenEl.classList.remove('invert');
  }

  // Render active face layout
  screenEl.innerHTML = renderFace(store.settings.face, store.settings.label !== false ? store.settings : { ...store.settings, label: false }, store.telemetry);
}

/**
 * Responsive Screen Scaler using ResizeObserver
 */
function initResponsiveScaler() {
  if (!previewAreaEl) return;

  const updateScale = () => {
    const rect = previewAreaEl.getBoundingClientRect();
    const padX = 48; // padding buffer
    const padY = 48;
    const availW = Math.max(200, rect.width - padX);
    const availH = Math.max(160, rect.height - padY);

    const scaleX = availW / 480;
    const scaleY = availH / 320;
    const scale = Math.min(scaleX, scaleY);
    const clampedScale = Math.min(2.0, Math.max(0.45, scale));

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
  document.querySelectorAll('.swatch-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const color = btn.dataset.color;
      document.querySelectorAll('.swatch-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      store.updateSettings({ accent: color });
      updateThumbnailsAccent();
    });
  });

  // Refresh Rate Segmented Control
  document.querySelectorAll('[data-refresh]').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-refresh]').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      store.updateSettings({ refresh: parseInt(btn.dataset.refresh, 10) });
    });
  });

  // Brightness Slider
  if (brightnessSlider) {
    brightnessSlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value, 10);
      if (brightnessValEl) brightnessValEl.textContent = `${val}%`;
      store.updateSettings({ brightness: val });
    });
  }

  // Toggles / Flags
  const bindToggle = (id, prop) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', (e) => {
        store.updateSettings({ [prop]: e.target.checked });
      });
    }
  };

  bindToggle('opt-label', 'label');
  bindToggle('opt-temp', 'temp');
  bindToggle('opt-units', 'units');
  bindToggle('opt-invert', 'invert');
  bindToggle('opt-auto', 'auto');

  // Window Controls
  const minBtn = document.getElementById('win-min');
  const maxBtn = document.getElementById('win-max');
  const closeBtn = document.getElementById('win-close');

  if (minBtn) minBtn.addEventListener('click', () => windowMinimize());
  if (maxBtn) maxBtn.addEventListener('click', () => windowMaximize());
  if (closeBtn) closeBtn.addEventListener('click', () => windowClose());

  // Flash Button
  if (flashBtn) {
    flashBtn.addEventListener('click', async () => {
      flashBtn.classList.add('flashing');
      if (flashStatusEl) flashStatusEl.textContent = 'FLASHING TO GADGET...';

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

        flashBtn.classList.remove('flashing');
        flashBtn.classList.add('flash-success');
        if (flashStatusEl) flashStatusEl.textContent = 'FLASHED SUCCESSFULLY ✓';

        setTimeout(() => {
          flashBtn.classList.remove('flash-success');
          if (flashStatusEl) flashStatusEl.textContent = 'READY';
        }, 2200);
      } catch (err) {
        flashBtn.classList.remove('flashing');
        if (flashStatusEl) flashStatusEl.textContent = `FLASH ERROR: ${err}`;
        setTimeout(() => {
          if (flashStatusEl) flashStatusEl.textContent = 'READY';
        }, 3000);
      }
    });
  }

  // Presets Save / Load
  const savePresetBtn = document.getElementById('preset-save');
  const loadPresetBtn = document.getElementById('preset-load');

  if (savePresetBtn) {
    savePresetBtn.addEventListener('click', async () => {
      try {
        await savePresetFile(store.settings);
        if (flashStatusEl) flashStatusEl.textContent = 'PRESET SAVED';
        setTimeout(() => {
          if (flashStatusEl) flashStatusEl.textContent = 'READY';
        }, 1500);
      } catch (e) {
        console.error('Preset save failed:', e);
      }
    });
  }

  if (loadPresetBtn) {
    loadPresetBtn.addEventListener('click', async () => {
      try {
        const loaded = await loadPresetFile();
        if (loaded) {
          store.updateSettings(loaded);
          // Sync UI
          if (brightnessSlider) brightnessSlider.value = store.settings.brightness;
          if (brightnessValEl) brightnessValEl.textContent = `${store.settings.brightness}%`;
          ['label', 'temp', 'units', 'invert', 'auto'].forEach((prop) => {
            const el = document.getElementById(`opt-${prop}`);
            if (el && store.settings[prop] !== undefined) el.checked = store.settings[prop];
          });
          updateThumbnailSelection();
          updateThumbnailsAccent();
          if (flashStatusEl) flashStatusEl.textContent = 'PRESET LOADED';
          setTimeout(() => {
            if (flashStatusEl) flashStatusEl.textContent = 'READY';
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
        if (connPillEl) connPillEl.classList.add('live');
        if (connStatusText) connStatusText.textContent = 'LIVE · 115200 BAUD';
      } else {
        if (connPillEl) connPillEl.classList.remove('live');
        if (connStatusText) connStatusText.textContent = 'OFFLINE';
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
  initFaceLibrary();
  initControls();
  initResponsiveScaler();

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
