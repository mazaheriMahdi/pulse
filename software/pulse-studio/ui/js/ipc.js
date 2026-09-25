/* ============================================================
   PULSE STUDIO — IPC Transport Layer (Tauri v2 + Mock Fallback)
   ============================================================ */

/**
 * Resolves the Tauri invoke function across v1, v2 and global variants.
 */
function getTauriInvoke() {
  if (window.__TAURI__ && window.__TAURI__.core && typeof window.__TAURI__.core.invoke === 'function') {
    return window.__TAURI__.core.invoke;
  }
  if (window.__TAURI__ && typeof window.__TAURI__.invoke === 'function') {
    return window.__TAURI__.invoke;
  }
  if (window.__TAURI_INTERNALS__ && typeof window.__TAURI_INTERNALS__.invoke === 'function') {
    return window.__TAURI_INTERNALS__.invoke;
  }
  return null;
}

export async function invokeCommand(cmd, args = {}) {
  const invoke = getTauriInvoke();
  if (invoke) {
    try {
      return await invoke(cmd, args);
    } catch (err) {
      console.warn(`[IPC] Tauri command "${cmd}" error:`, err);
      throw err;
    }
  } else {
    // Development browser mock fallback
    if (cmd === 'get_boot_status') {
      return window.__MOCK_BOOT_STATUS__ || {
        step: 5,
        label: 'CONNECTED',
        detail: 'PULSE hardware locked & synced ✓',
        is_connected: true,
      };
    }
    if (cmd === 'is_daemon_connected') {
      return true;
    }
    if (cmd === 'get_telemetry') {
      return {
        cpu: Math.floor(35 + Math.random() * 20),
        cpu_temp: Math.floor(52 + Math.random() * 8),
        gpu: Math.floor(45 + Math.random() * 25),
        gpu_temp: Math.floor(48 + Math.random() * 10),
        ram: 62,
        battery: 100,
        net_up: 12,
        net_dn: 84,
        peak_up: 48,
        peak_dn: 212,
        iface: 'ETH0',
      };
    }
    if (cmd === 'send_config') {
      console.log('[IPC Mock] send_config payload:', args);
      return 'FLASH_ACK';
    }
    if (cmd === 'save_preset') {
      localStorage.setItem('pulse_preset', JSON.stringify(args.preset));
      return 'SAVED';
    }
    if (cmd === 'load_preset') {
      const stored = localStorage.getItem('pulse_preset');
      return stored ? JSON.parse(stored) : null;
    }
    return null;
  }
}

export async function fetchBootStatus() {
  return await invokeCommand('get_boot_status');
}

export async function fetchTelemetry() {
  return await invokeCommand('get_telemetry');
}

export async function checkDaemonConnected() {
  return await invokeCommand('is_daemon_connected');
}

export async function flashConfigToGadget(config) {
  return await invokeCommand('send_config', { config });
}

export async function savePresetFile(preset) {
  return await invokeCommand('save_preset', { preset });
}

export async function loadPresetFile() {
  return await invokeCommand('load_preset');
}

export async function windowMinimize() {
  return await invokeCommand('minimize_window');
}

export async function windowMaximize() {
  return await invokeCommand('maximize_window');
}

export async function windowClose() {
  return await invokeCommand('close_window');
}
