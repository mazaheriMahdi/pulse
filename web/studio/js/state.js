/* ============================================================
   PULSE STUDIO — Reactive State Store
   ============================================================ */

import { DEFAULT_SETTINGS, INITIAL_TELEMETRY } from './constants.js';

class StateStore {
  constructor() {
    this.settings = { ...DEFAULT_SETTINGS };
    this.telemetry = { ...INITIAL_TELEMETRY };
    this.isConnected = false;
    this.listeners = new Set();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify(changeType) {
    for (const listener of this.listeners) {
      try {
        listener(this, changeType);
      } catch (err) {
        console.error('[State] Listener error:', err);
      }
    }
  }

  updateSettings(partial) {
    this.settings = { ...this.settings, ...partial };
    this.notify('settings');
  }

  updateTelemetry(partial) {
    this.telemetry = { ...this.telemetry, ...partial };
    this.notify('telemetry');
  }

  setConnection(connected) {
    if (this.isConnected !== connected) {
      this.isConnected = connected;
      this.notify('connection');
    }
  }
}

export const store = new StateStore();
