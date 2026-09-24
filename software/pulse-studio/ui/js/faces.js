/* ============================================================
   PULSE STUDIO — Face Renderers
   Matches 480×320 Hardware TFT LCD pixel-for-pixel
   ============================================================ */

import { renderNdot, renderDotBar } from './font.js';

/**
 * Format 2-digit number with leading zero if needed
 */
function pad2(num) {
  const n = Math.max(0, Math.min(99, Math.round(num || 0)));
  return n < 10 ? `0${n}` : `${n}`;
}

/**
 * CPU / GPU Grid (Single Gauge Layout)
 */
export function renderSingleGauge(title, meta, val, temp, settings) {
  const showLabel = settings.label !== false;
  const showTemp = settings.temp !== false;
  const showUnits = settings.units !== false;
  const isHot = val >= 85 || temp >= 80;

  const headerHtml = showLabel
    ? `<div class="face-topbar">
        <div class="header-tag">${renderNdot(title, 3)}</div>
        <div class="header-meta">${meta}</div>
      </div>`
    : '';

  const unitsSvg = showUnits ? renderNdot('%', 5, 'val-unit') : '';

  const tempBlockHtml = showTemp
    ? `<div class="single-bottom-block">
        <div class="sub-lbl">T &nbsp;E &nbsp;M &nbsp;P</div>
        <div style="display:flex;align-items:baseline;gap:4px">
          ${renderNdot(pad2(temp), 7)}
          ${showUnits ? renderNdot('°C', 4, 'temp-unit') : ''}
        </div>
      </div>`
    : '<div></div>';

  const statusText = temp >= 80 ? 'CRIT' : temp >= 65 ? 'BOOST' : 'NORMAL';

  return `
    <div class="face-viewport single-container">
      ${headerHtml}
      <div class="hairline-h"></div>

      <div class="single-val-row">
        ${renderNdot(pad2(val), 11, 'big-num')}
        ${unitsSvg}
      </div>

      <div class="dotbar-container" style="margin: 12px 0;">
        ${renderDotBar(val, 28, isHot)}
      </div>

      <div class="hairline-h"></div>

      <div class="single-bottom-row">
        ${tempBlockHtml}
        <div class="single-bottom-block" style="align-items:flex-end">
          <div class="sub-lbl">S &nbsp;T &nbsp;A &nbsp;T &nbsp;U &nbsp;S</div>
          <div style="margin-top:2px;">
            ${renderNdot(statusText, 3, isHot ? 'text-red' : '')}
          </div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Dual Load Layout (CPU + GPU side-by-side) — The Reference Standard
 */
export function renderDualLoad(telemetry, settings) {
  const showLabel = settings.label !== false;
  const showTemp = settings.temp !== false;
  const showUnits = settings.units !== false;

  const cpuVal = telemetry.cpu || 0;
  const cpuTemp = telemetry.cpuT || telemetry.cpu_temp || 0;
  const gpuVal = telemetry.gpu || 0;
  const gpuTemp = telemetry.gpuT || telemetry.gpu_temp || 0;

  const isCpuHot = cpuVal >= 85 || cpuTemp >= 80;
  const isGpuHot = gpuVal >= 85 || gpuTemp >= 80;

  const cpuHeader = showLabel
    ? `<div class="column-header">
        <div class="col-title">${renderNdot('CPU', 3)}</div>
        <div class="col-meta">4.2 GHZ</div>
      </div>`
    : '';

  const gpuHeader = showLabel
    ? `<div class="column-header">
        <div class="col-title">${renderNdot('GPU', 3)}</div>
        <div class="col-meta">185 W</div>
      </div>`
    : '';

  const cpuTempHtml = showTemp
    ? `<div class="temp-footer-row">
        <span class="lbl">T &nbsp;E &nbsp;M &nbsp;P</span>
        <div style="display:flex;align-items:baseline;gap:2px">
          ${renderNdot(pad2(cpuTemp), 7)}
          ${showUnits ? renderNdot('°C', 3, 'temp-unit') : ''}
        </div>
      </div>`
    : '';

  const gpuTempHtml = showTemp
    ? `<div class="temp-footer-row">
        <span class="lbl">T &nbsp;E &nbsp;M &nbsp;P</span>
        <div style="display:flex;align-items:baseline;gap:2px">
          ${renderNdot(pad2(gpuTemp), 7)}
          ${showUnits ? renderNdot('°C', 3, 'temp-unit') : ''}
        </div>
      </div>`
    : '';

  return `
    <div class="face-viewport">
      <div class="dual-container">
        <!-- CPU COLUMN -->
        <div class="dual-column">
          ${cpuHeader}
          <div class="hairline-h"></div>
          <div class="val-center-row">
            ${renderNdot(pad2(cpuVal), 11, 'big-num')}
            ${showUnits ? renderNdot('%', 5, 'val-unit') : ''}
          </div>
          <div class="dotbar-container" style="margin: 8px 0;">
            ${renderDotBar(cpuVal, 24, isCpuHot)}
          </div>
          <div class="hairline-h"></div>
          ${cpuTempHtml}
        </div>

        <!-- VERTICAL DIVIDER -->
        <div class="hairline-v"></div>

        <!-- GPU COLUMN -->
        <div class="dual-column">
          ${gpuHeader}
          <div class="hairline-h"></div>
          <div class="val-center-row">
            ${renderNdot(pad2(gpuVal), 11, 'big-num')}
            ${showUnits ? renderNdot('%', 5, 'val-unit') : ''}
          </div>
          <div class="dotbar-container" style="margin: 8px 0;">
            ${renderDotBar(gpuVal, 24, isGpuHot)}
          </div>
          <div class="hairline-h"></div>
          ${gpuTempHtml}
        </div>
      </div>
    </div>
  `;
}

/**
 * Memory Layout (Dual 20-dot bars for USED and FREE)
 */
export function renderMemory(telemetry, settings) {
  const showLabel = settings.label !== false;
  const showUnits = settings.units !== false;
  const ramPct = telemetry.ram || 0;
  const totalGb = 32.0;
  const usedGb = (totalGb * (ramPct / 100)).toFixed(1);
  const freeGb = (totalGb - usedGb).toFixed(1);
  const isHot = ramPct >= 85;

  const headerHtml = showLabel
    ? `<div class="face-topbar">
        <div class="header-tag">${renderNdot('MEMORY', 3)}</div>
        <div class="header-meta">32 GB DDR5</div>
      </div>`
    : '';

  return `
    <div class="face-viewport">
      ${headerHtml}
      <div class="hairline-h"></div>

      <div style="display:flex;align-items:baseline;justify-content:space-between;margin:4px 0;">
        <div style="display:flex;align-items:baseline;gap:6px">
          ${renderNdot(pad2(ramPct), 11, 'big-num')}
          ${showUnits ? renderNdot('%', 5, 'val-unit') : ''}
        </div>
        <div style="font-family:var(--font-mono);font-size:10px;font-weight:700;letter-spacing:0.18em;color:#6a6a6a;">
          RAM IN USE
        </div>
      </div>

      <div class="hairline-h"></div>

      <div class="memory-stack">
        <div class="memory-row">
          <div class="mem-lbl">${renderNdot('USED', 2)}</div>
          <div style="flex:1;">${renderDotBar(ramPct, 20, isHot)}</div>
          <div class="mem-val">${usedGb} GB</div>
        </div>

        <div class="hairline-h"></div>

        <div class="memory-row">
          <div class="mem-lbl" style="opacity:0.6;">${renderNdot('FREE', 2)}</div>
          <div style="flex:1;">${renderDotBar(100 - ramPct, 20, false)}</div>
          <div class="mem-val">${freeGb} GB</div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Thermal Layout (Dual Temperature Gauges)
 */
export function renderThermal(telemetry, settings) {
  const showLabel = settings.label !== false;
  const showUnits = settings.units !== false;

  const cpuTemp = telemetry.cpuT || telemetry.cpu_temp || 0;
  const gpuTemp = telemetry.gpuT || telemetry.gpu_temp || 0;

  const isCpuHot = cpuTemp >= 80;
  const isGpuHot = gpuTemp >= 80;

  const cpuStatus = cpuTemp >= 80 ? 'CRIT' : cpuTemp >= 65 ? 'WARM' : 'NORMAL';
  const gpuStatus = gpuTemp >= 80 ? 'CRIT' : gpuTemp >= 65 ? 'WARM' : 'NORMAL';

  const cpuHeader = showLabel
    ? `<div class="column-header">
        <div class="col-title">${renderNdot('CPU', 3)}</div>
        <div class="col-meta">TCTL</div>
      </div>`
    : '';

  const gpuHeader = showLabel
    ? `<div class="column-header">
        <div class="col-title">${renderNdot('GPU', 3)}</div>
        <div class="col-meta">EDGE</div>
      </div>`
    : '';

  return `
    <div class="face-viewport">
      <div class="dual-container">
        <!-- CPU THERMAL -->
        <div class="dual-column">
          ${cpuHeader}
          <div class="hairline-h"></div>
          <div class="val-center-row">
            ${renderNdot(pad2(cpuTemp), 11, isCpuHot ? 'text-red' : '')}
            ${showUnits ? renderNdot('°C', 5, 'val-unit') : ''}
          </div>
          <div class="dotbar-container" style="margin: 8px 0;">
            ${renderDotBar(cpuTemp, 24, isCpuHot)}
          </div>
          <div class="hairline-h"></div>
          <div class="temp-footer-row">
            <span class="lbl">T H E R M A L</span>
            <div style="margin-top:2px;">
              ${renderNdot(cpuStatus, 2, isCpuHot ? 'text-red' : '')}
            </div>
          </div>
        </div>

        <!-- VERTICAL DIVIDER -->
        <div class="hairline-v"></div>

        <!-- GPU THERMAL -->
        <div class="dual-column">
          ${gpuHeader}
          <div class="hairline-h"></div>
          <div class="val-center-row">
            ${renderNdot(pad2(gpuTemp), 11, isGpuHot ? 'text-red' : '')}
            ${showUnits ? renderNdot('°C', 5, 'val-unit') : ''}
          </div>
          <div class="dotbar-container" style="margin: 8px 0;">
            ${renderDotBar(gpuTemp, 24, isGpuHot)}
          </div>
          <div class="hairline-h"></div>
          <div class="temp-footer-row">
            <span class="lbl">T H E R M A L</span>
            <div style="margin-top:2px;">
              ${renderNdot(gpuStatus, 2, isGpuHot ? 'text-red' : '')}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Minimal Layout
 */
export function renderMinimal(telemetry, settings) {
  const showUnits = settings.units !== false;
  const cpuVal = telemetry.cpu || 0;

  return `
    <div class="face-viewport minimal-container">
      <div style="margin-top: 4px;">
        ${renderNdot('PULSE', 2)}
      </div>

      <div class="hairline-h"></div>

      <div style="display:flex;align-items:baseline;justify-content:center;gap:8px;margin: 12px 0;">
        ${renderNdot(pad2(cpuVal), 11, 'big-num')}
        ${showUnits ? renderNdot('%', 5, 'val-unit') : ''}
      </div>

      <div class="dotbar-container" style="width: 85%; margin: 6px 0;">
        ${renderDotBar(cpuVal, 28, cpuVal >= 85)}
      </div>

      <div class="hairline-h"></div>

      <div style="margin-bottom: 4px;">
        ${renderNdot('LOAD', 3)}
      </div>
    </div>
  `;
}

/**
 * Master face router
 */
export function renderFace(faceId, settings, telemetry) {
  switch (faceId) {
    case 'cpu':
      return renderSingleGauge('CPU', '4.2 GHZ', telemetry.cpu || 0, telemetry.cpuT || telemetry.cpu_temp || 0, settings);
    case 'gpu':
      return renderSingleGauge('GPU', '185 W', telemetry.gpu || 0, telemetry.gpuT || telemetry.gpu_temp || 0, settings);
    case 'ram':
    case 'memory':
      return renderMemory(telemetry, settings);
    case 'thermal':
      return renderThermal(telemetry, settings);
    case 'minimal':
      return renderMinimal(telemetry, settings);
    case 'dual':
    default:
      return renderDualLoad(telemetry, settings);
  }
}
