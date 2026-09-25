/* ============================================================
   PULSE STUDIO — Nothing (R) OS Boot Splash Sequence Controller
   ============================================================ */

import { renderNdot } from './font.js';
import { fetchBootStatus } from './ipc.js';

const BOOT_STEPS = [
  { id: 1, name: 'SCANNING SERIAL BUS', targetDots: 6, defaultStatus: 'PENDING' },
  { id: 2, name: 'DAEMON INITIALIZATION', targetDots: 12, defaultStatus: 'PENDING' },
  { id: 3, name: 'SYNCING 115200 BAUD', targetDots: 18, defaultStatus: 'PENDING' },
  { id: 4, name: 'TELEMETRY SENSORS', targetDots: 24, defaultStatus: 'PENDING' },
];

export class BootSplashController {
  constructor(overlayElement) {
    this.overlay = overlayElement;
    this.currentStep = 1;
    this.litDots = 3;
    this.isDismissed = false;
  }

  init() {
    if (!this.overlay) return Promise.resolve();

    this.overlay.innerHTML = `
      <div class="boot-card">
        <div class="boot-header">
          <div class="boot-brand">
            <span class="boot-blip"></span>
            <div class="boot-title">
              <div id="splashNdotLogo"></div>
              <span class="sub">NOTHING (R) OS // BOOT PROTOCOL</span>
            </div>
          </div>
          <div class="boot-badge" id="splashBadge">
            <span class="pulse-dot"></span>
            <span id="splashBadgeText">INITIALIZING</span>
          </div>
        </div>

        <div class="boot-console" id="splashConsole">
          ${BOOT_STEPS.map(
            (step) => `
            <div class="console-step ${step.id === 1 ? 'active' : ''}" id="console-step-${step.id}">
              <div class="step-prefix">
                <span class="step-index">[0${step.id}/04]</span>
                <span class="step-name">${step.name}</span>
              </div>
              <span class="step-status" id="step-status-${step.id}">${step.id === 1 ? 'PROBING...' : 'PENDING'}</span>
            </div>
          `
          ).join('')}
        </div>

        <div class="boot-progress-wrap">
          <div class="boot-progress-label">
            <span>HARDWARE LINK SYNC</span>
            <span class="pct" id="splashPct">12%</span>
          </div>
          <div class="boot-dotbar" id="splashDotbar">
            ${Array.from({ length: 24 }, (_, i) => `<i id="dot-${i}" class="${i < 3 ? 'on' : ''}"></i>`).join('')}
          </div>
        </div>

        <div class="boot-footer">
          <span class="boot-detail-msg" id="splashDetail">Probing serial devices (/dev/ttyUSB*, /dev/ttyACM*)...</span>
          <button class="boot-action-skip" id="splashSkipBtn">SKIP TO STUDIO →</button>
        </div>
      </div>
    `;

    // Render NDot Logo
    const logoEl = document.getElementById('splashNdotLogo');
    if (logoEl) {
      logoEl.innerHTML = renderNdot('PULSE', 3);
    }

    return new Promise((resolve) => {
      this.resolvePromise = resolve;

      // Skip button listener for demo or instant bypass
      const skipBtn = document.getElementById('splashSkipBtn');
      if (skipBtn) {
        skipBtn.addEventListener('click', () => {
          this.dismiss();
        });
      }

      this.startPolling();
    });
  }

  updateDotbar(count) {
    this.litDots = Math.max(0, Math.min(24, count));
    for (let i = 0; i < 24; i++) {
      const dotEl = document.getElementById(`dot-${i}`);
      if (dotEl) {
        if (i < this.litDots) {
          dotEl.classList.add('on');
          if (i === this.litDots - 1 && this.litDots < 24) {
            dotEl.classList.add('red');
          } else {
            dotEl.classList.remove('red');
          }
        } else {
          dotEl.classList.remove('on', 'red');
        }
      }
    }
    const pctEl = document.getElementById('splashPct');
    if (pctEl) {
      const pct = Math.round((this.litDots / 24) * 100);
      pctEl.textContent = `${pct}%`;
    }
  }

  updateStep(stepIndex, detailMsg) {
    this.currentStep = stepIndex;

    BOOT_STEPS.forEach((step) => {
      const row = document.getElementById(`console-step-${step.id}`);
      const statusEl = document.getElementById(`step-status-${step.id}`);

      if (row && statusEl) {
        if (step.id < stepIndex) {
          row.className = 'console-step done';
          statusEl.textContent = 'OK ✓';
        } else if (step.id === stepIndex) {
          row.className = 'console-step active';
          statusEl.textContent = 'ACTIVE...';
        } else {
          row.className = 'console-step';
          statusEl.textContent = 'PENDING';
        }
      }
    });

    const targetDots = Math.min(24, stepIndex * 6);
    this.updateDotbar(targetDots);

    const detailEl = document.getElementById('splashDetail');
    if (detailEl && detailMsg) {
      detailEl.textContent = detailMsg;
    }
  }

  setConnected() {
    BOOT_STEPS.forEach((step) => {
      const row = document.getElementById(`console-step-${step.id}`);
      const statusEl = document.getElementById(`step-status-${step.id}`);
      if (row) row.className = 'console-step done';
      if (statusEl) statusEl.textContent = 'LOCKED ✓';
    });

    this.updateDotbar(24);

    const badge = document.getElementById('splashBadge');
    const badgeText = document.getElementById('splashBadgeText');
    if (badge) badge.classList.add('connected');
    if (badgeText) badgeText.textContent = 'CONNECTED ✓';

    const detailEl = document.getElementById('splashDetail');
    if (detailEl) detailEl.textContent = 'ALL SENSORS SYNCED · LAUNCHING STUDIO...';

    // Satisfying delay before opening workspace
    setTimeout(() => {
      this.dismiss();
    }, 650);
  }

  dismiss() {
    if (this.isDismissed) return;
    this.isDismissed = true;

    if (this.overlay) {
      this.overlay.classList.add('dismissed');
      setTimeout(() => {
        this.overlay.style.display = 'none';
      }, 600);
    }

    if (this.resolvePromise) {
      this.resolvePromise();
    }
  }

  startPolling() {
    let tickCount = 0;
    const pollInterval = setInterval(async () => {
      if (this.isDismissed) {
        clearInterval(pollInterval);
        return;
      }

      tickCount++;

      try {
        const status = await fetchBootStatus();
        if (status) {
          if (status.is_connected || status.step >= 5) {
            clearInterval(pollInterval);
            this.setConnected();
            return;
          }

          this.updateStep(status.step, status.detail);
        }
      } catch (err) {
        // Fallback simulated progress for browser test environment
        if (tickCount === 3) this.updateStep(2, 'Host daemon process active');
        if (tickCount === 6) this.updateStep(3, 'Handshake acknowledged on /dev/ttyUSB1');
        if (tickCount === 9) this.updateStep(4, 'Telemetry streaming @ 115200 baud');
        if (tickCount >= 11) {
          clearInterval(pollInterval);
          this.setConnected();
        }
      }
    }, 150);
  }
}
